import time
import jwt
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="FDE Enterprise RBAC Gateway")
security = HTTPBearer()

# In production with Keycloak/Okta, fetch public RS256 key from JWKS URI.
# For zero-setup local testing, we use a shared secret or local RSA keypair:
JWT_SECRET = "enterprise-oidc-signing-key-demo"
JWT_ALGO = "HS256"

@app.post("/auth/mock-idp-token")
def issue_test_jwt(username: str = "nilesh.fde", roles: List[str] = ["ops_viewer"]):
    """Simulates Keycloak/Okta token endpoint issuing a short-lived JWT with realm roles."""
    payload = {
        "sub": username,
        "iss": "https://idp.enterprise.internal/realms/main",
        "realm_access": {"roles": roles},
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return {"access_token": token, "token_type": "Bearer", "assigned_roles": roles}

def verify_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT token expired")
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid JWT: {err}")

def get_current_user_claims(creds: HTTPAuthorizationCredentials = Security(security)) -> dict:
    return verify_access_token(creds.credentials)

def get_verified_roles(claims: dict) -> List[str]:
    realm_access = claims.get("realm_access")
    roles = realm_access.get("roles") if isinstance(realm_access, dict) else None
    if not isinstance(roles, list) or not all(
        isinstance(role, str) and role for role in roles
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JWT does not contain valid realm roles",
        )
    return roles

def require_roles(allowed_roles: List[str]):
    """Reusable FastAPI dependency factory for route-level RBAC enforcement."""
    def role_checker(claims: dict = Depends(get_current_user_claims)):
        user_roles = get_verified_roles(claims)
        if not any(r in allowed_roles for r in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"RBAC Policy Block: Requires one of {allowed_roles}, caller has {user_roles}"
            )
        return claims
    return role_checker

@app.get("/api/v1/incidents")
def list_incidents(claims: dict = Depends(require_roles(["ops_viewer", "sec_auditor", "fde_admin"]))):
    return {"viewer": claims["sub"], "incidents": [{"id": "INC-101", "status": "OPEN"}]}

@app.post("/api/v1/admin/remediation-trigger")
def trigger_remediation(claims: dict = Depends(require_roles(["fde_admin"]))):
    return {"status": "REMEDIATION_EXECUTED", "authorized_by": claims["sub"]}