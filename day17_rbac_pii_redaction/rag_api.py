"""JWT-protected API for role-filtered hybrid document retrieval."""

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from day4_oidc_and_rbac.rbac_auth_service import (
    get_current_user_claims,
    get_verified_roles,
)
from day15_16_hybrid_search_rag.hybrid_rag_rrf import answer_query

app = FastAPI(title="Role-protected document search")


class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    role: str | None = None


@app.post("/api/v1/documents/ask")
def ask_documents(
    request: AskRequest,
    claims: dict = Depends(get_current_user_claims),
) -> dict[str, str]:
    roles = get_verified_roles(claims)
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JWT does not grant a document-search role",
        )

    if request.role is None:
        if len(roles) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Select one role from the verified JWT roles",
            )
        verified_role = roles[0]
    elif request.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requested role is not present in the verified JWT",
        )
    else:
        verified_role = request.role

    return {"answer": answer_query(request.query, verified_role)}
