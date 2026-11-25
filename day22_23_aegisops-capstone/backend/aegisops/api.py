"""FastAPI application for role-aware incident analysis."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Awaitable, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request as FastAPIRequest,
    Response,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from prometheus_fastapi_instrumentator import Instrumentator

from aegisops.assistant import (
    AskService,
    ChatCompletion,
    MarkdownRetriever,
    PostgresRetrievalError,
    PostgresVectorRetriever,
    UnsafeQueryError,
)
from aegisops.ingestion import OpenAICompatibleEmbedder
from aegisops.metrics import CircuitOpenError, InstrumentedChatClient, Telemetry


class Role(str, Enum):
    SRE_LEAD = "sre_lead"
    TIER1_SUPPORT = "tier1_support"
    EXTERNAL_AUDITOR = "external_auditor"


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    demo_token_issuer_enabled: bool
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    database_path: str
    runbooks_directory: str
    redacted_postmortems_directory: str | None
    neon_database_url: str | None
    embedding_model: str
    embedding_dimensions: int
    input_cost_per_million: float
    output_cost_per_million: float
    jwt_ttl_seconds: int = 1800

    @classmethod
    def from_environment(cls) -> Settings:
        postmortems_dir = os.environ.get("REDACTED_POSTMORTEMS_DIR", "").strip()
        return cls(
            jwt_secret=os.environ.get("JWT_SECRET", ""),
            demo_token_issuer_enabled=os.environ.get(
                "DEMO_TOKEN_ISSUER_ENABLED", ""
            ).lower()
            in {"1", "true", "yes"},
            llm_api_key=os.environ.get("OPENAI_API_KEY", ""),
            llm_base_url=os.environ.get(
                "OPENAI_BASE_URL", "https://api.openai.com/v1"
            ).rstrip("/"),
            llm_model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            database_path=os.environ.get(
                "DUCKDB_PATH", "data_seed/generated/aegisops.duckdb"
            ),
            runbooks_directory=os.environ.get(
                "RUNBOOKS_DIR", "data_seed/runbooks"
            ),
            redacted_postmortems_directory=postmortems_dir or None,
            neon_database_url=os.environ.get("POSTMORTEM_DATABASE_URL")
            or os.environ.get("NEON_DATABASE_URL")
            or os.environ.get("DATABASE_URL"),
            embedding_model=os.environ.get(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
            embedding_dimensions=int(
                os.environ.get("OPENAI_EMBEDDING_DIMENSIONS", "1536")
            ),
            input_cost_per_million=float(
                os.environ.get("LLM_INPUT_COST_PER_1M", "0")
            ),
            output_cost_per_million=float(
                os.environ.get("LLM_OUTPUT_COST_PER_1M", "0")
            ),
        )


@dataclass(frozen=True)
class Completion:
    content: str
    prompt_tokens: int
    completion_tokens: int


class LLMUnavailableError(RuntimeError):
    pass


class OpenAICompatibleChatClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 30,
    ) -> None:
        self._api_key = api_key
        self._url = f"{base_url}/chat/completions"
        self._model = model
        self._timeout_seconds = timeout_seconds

    def complete(self, prompt: str) -> ChatCompletion:
        if not self._api_key:
            raise LLMUnavailableError("OPENAI_API_KEY is required for incident synthesis")
        request_body = json.dumps(
            {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            }
        ).encode("utf-8")
        for attempt in range(2):
            request = Request(
                self._url,
                data=request_body,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=self._timeout_seconds) as response:
                    payload = json.load(response)
                break
            except HTTPError as error:
                if error.code == 503 and attempt == 0:
                    time.sleep(0.5)
                    continue
                raise LLMUnavailableError(
                    f"LLM service returned HTTP {error.code}"
                ) from error
            except URLError as error:
                raise LLMUnavailableError(
                    f"Could not reach the LLM service: {error.reason}"
                ) from error
        try:
            message = payload["choices"][0]["message"]["content"]
            usage = payload["usage"]
            return Completion(
                content=message,
                prompt_tokens=int(usage["prompt_tokens"]),
                completion_tokens=int(usage["completion_tokens"]),
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise LLMUnavailableError("LLM service returned an invalid response") from error


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, question: str) -> str:
        normalized = question.strip()
        if len(normalized) < 3:
            raise ValueError("The question must contain at least three non-space characters")
        return normalized


class AskResponse(BaseModel):
    answer: str
    sql_query: str
    sql_results: list[dict[str, object]]
    sources: list[str]


class DemoTokenRequest(BaseModel):
    role: Role


class DemoTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    role: Role


def create_app(
    settings: Settings | None = None,
    ask_service: AskService | None = None,
) -> FastAPI:
    config = settings or Settings.from_environment()
    telemetry = Telemetry(
        cost_pricing_configured=(
            config.input_cost_per_million > 0 or config.output_cost_per_million > 0
        )
    )
    vector_retriever = None
    if config.neon_database_url and config.llm_api_key:
        vector_retriever = PostgresVectorRetriever(
            config.neon_database_url,
            OpenAICompatibleEmbedder(
                api_key=config.llm_api_key,
                model=config.embedding_model,
                dimensions=config.embedding_dimensions,
                base_url=config.llm_base_url,
            ),
        )
    app = FastAPI(title="AegisOps Incident Assistant", version="1.0.0")
    app.state.telemetry = telemetry
    app.state.ask_service = ask_service or AskService(
        chat=InstrumentedChatClient(
            OpenAICompatibleChatClient(
                config.llm_api_key, config.llm_base_url, config.llm_model
            ),
            telemetry,
            input_cost_per_million=config.input_cost_per_million,
            output_cost_per_million=config.output_cost_per_million,
        ),
        retriever=MarkdownRetriever(
            config.runbooks_directory,
            config.redacted_postmortems_directory,
            vector_retriever=vector_retriever,
        ),
        database_path=config.database_path,
    )
    bearer = HTTPBearer(auto_error=False)

    @app.middleware("http")
    async def record_latency(
        request: FastAPIRequest,
        call_next: Callable[[FastAPIRequest], Awaitable[Response]],
    ) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        telemetry.record_request(time.monotonic() - start)
        return response

    def current_role(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> Role:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A bearer token is required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if len(config.jwt_secret.encode("utf-8")) < 32:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="JWT_SECRET must contain at least 32 bytes",
            )
        try:
            claims = jwt.decode(
                credentials.credentials,
                config.jwt_secret,
                algorithms=["HS256"],
                issuer="aegisops-demo",
                audience="aegisops-api",
                options={"require": ["exp", "iat", "iss", "aud", "sub", "role"]},
            )
            return Role(claims["role"])
        except (jwt.InvalidTokenError, ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The bearer token is invalid or expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

    @app.post("/api/v1/demo/token", response_model=DemoTokenResponse)
    def mint_demo_token(payload: DemoTokenRequest) -> DemoTokenResponse:
        if not config.demo_token_issuer_enabled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Demo token issuance is disabled",
            )
        if len(config.jwt_secret.encode("utf-8")) < 32:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configure JWT_SECRET with at least 32 bytes",
            )
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=config.jwt_ttl_seconds)
        token = jwt.encode(
            {
                "sub": f"demo:{payload.role.value}",
                "role": payload.role.value,
                "iss": "aegisops-demo",
                "aud": "aegisops-api",
                "iat": now,
                "exp": expires_at,
            },
            config.jwt_secret,
            algorithm="HS256",
        )
        return DemoTokenResponse(
            access_token=token, expires_at=expires_at, role=payload.role
        )

    @app.post("/api/v1/ask", response_model=AskResponse)
    def ask(
        payload: AskRequest,
        role: Role = Depends(current_role),
    ) -> AskResponse:
        try:
            result = app.state.ask_service.ask(payload.question, role.value)
        except CircuitOpenError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
            ) from error
        except LLMUnavailableError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)
            ) from error
        except UnsafeQueryError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The metrics agent produced a disallowed query",
            ) from error
        except PostgresRetrievalError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Semantic post-mortem retrieval is unavailable",
            ) from error
        return AskResponse(**result)

    @app.get("/api/v1/control-plane")
    def control_plane(
        _: Role = Depends(current_role),
    ) -> dict[str, float | int | bool | None | str]:
        try:
            pii_count = app.state.ask_service.redacted_entity_count()
        except PostgresRetrievalError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Post-mortem index telemetry is unavailable",
            ) from error
        return telemetry.snapshot(pii_count)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    Instrumentator().instrument(app).expose(app, include_in_schema=False)
    return app


app = create_app()