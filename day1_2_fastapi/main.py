import uuid
import time
import structlog
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

# Configure SRE-grade structured JSON logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
log = structlog.get_logger()

app = FastAPI(title="FDE Enterprise Ingestion API", version="1.0.0")

# 1. ASGI Correlation ID & Latency Middleware
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        corr_id = request.headers.get("X-Correlation-ID", f"fde-{uuid.uuid4().hex[:12]}")
        request.state.correlation_id = corr_id
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Correlation-ID"] = corr_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        
        log.info(
            "http_request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            correlation_id=corr_id
        )
        return response

app.add_middleware(CorrelationIdMiddleware)

# 2. Strict Pydantic v2 Data Contract with Dirty-Data Normalization
class LegacyIncidentPayload(BaseModel):
    tenant_id: str = Field(..., min_length=2, description="Enterprise client identifier")
    raw_severity: str = Field(..., description="Dirty severity string from client ERP")
    service_name: str = Field(..., min_length=2)
    error_message: str
    tags: Optional[List[str]] = Field(default_factory=list)
    reported_at: Optional[str] = None

    @field_validator("raw_severity")
    @classmethod
    def normalize_severity(cls, v: str) -> str:
        clean = v.strip().upper()
        mapping = {
            "SEV1": "CRITICAL", "P1": "CRITICAL", "CRITICAL": "CRITICAL", "1": "CRITICAL",
            "SEV2": "HIGH", "P2": "HIGH", "HIGH": "HIGH", "2": "HIGH",
            "SEV3": "MEDIUM", "P3": "MEDIUM", "WARN": "MEDIUM",
            "SEV4": "LOW", "INFO": "LOW"
        }
        if clean not in mapping:
            raise ValueError(f"Unrecognized client severity '{v}'. Expected P1-P3 or SEV1-SEV4.")
        return mapping[clean]

    @field_validator("tenant_id")
    @classmethod
    def normalize_tenant(cls, v: str) -> str:
        return v.strip().lower().replace(" ", "_")

# In-memory store + Dead-Letter store for rapid FDE demo
VALID_INCIDENTS = []

@app.get("/healthz")
async def healthcheck():
    return {"status": "healthy", "ingested_count": len(VALID_INCIDENTS)}

@app.post("/api/v1/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_incident(payload: LegacyIncidentPayload, request: Request):
    record = payload.model_dump()
    record["correlation_id"] = request.state.correlation_id
    record["ingested_at_utc"] = datetime.utcnow().isoformat()
    VALID_INCIDENTS.append(record)
    return {"status": "ingested", "normalized_record": record}