# Day 4: OIDC and RBAC Security Gateway

## Overview
This module demonstrates a lightweight identity and authorization layer using JWTs and role-based access control (RBAC). It simulates an enterprise gateway that validates bearer tokens and restricts access to protected API routes based on assigned roles.

## Business purpose
Modern internal services rarely trust anonymous requests. This example models a minimal identity-aware API gateway where:
- a test IdP issues JWTs
- client requests present a Bearer token
- the API verifies the token signature and expiration
- route access is permission-gated by roles like `ops_viewer`, `sec_auditor`, and `fde_admin`

## Key components

### FastAPI application
The app is created with `FastAPI` and exposes:
- `POST /auth/mock-idp-token` to mint a demo JWT
- `GET /api/v1/incidents` for viewing incidents
- `POST /api/v1/admin/remediation-trigger` for privileged admin actions

### JWT issuance
The `issue_test_jwt` route simulates a real IdP token endpoint. It creates a signed JWT with claims such as:
- `sub` (username)
- `iss` (issuer)
- `realm_access.roles` (roles assigned to the user)
- `exp` (expiration timestamp)

For local demos, the code uses a shared HS256 secret instead of a production JWKS-backed validation flow.

### Token validation
`get_current_user_claims` decodes the token using the configured secret and algorithm. It returns structured claims only when the token is valid and not expired.

Failure modes include:
- expired token
- invalid token or malformed signature
- missing or non-Bearer credentials

### Role enforcement
`get_verified_roles` extracts role strings from claims returned by `get_current_user_claims`. `require_roles` is a reusable dependency factory that checks whether the caller has any role required by the route. If the user lacks the needed permission, the API returns a `403 Forbidden` response.

This pattern allows route-level RBAC without duplicating logic in every endpoint.

## Security model
The example follows a simple policy model:
- `ops_viewer` can read incidents
- `sec_auditor` can read incidents
- `fde_admin` can trigger remediation actions

A route requiring any of the allowed roles is accepted only when the token contains those claims. If the user lacks the necessary permissions, the request is rejected with a clear RBAC policy error.

## Request flow
1. The client requests a token from `/auth/mock-idp-token` with a username and role list.
2. The server creates a JWT with the user identity and realm roles.
3. The client calls a protected route with the JWT in the `Authorization: Bearer ...` header.
4. FastAPI validates the token signature and expiration.
5. The role-check dependency confirms whether the assigned roles satisfy the route policy.
6. The protected action executes only when authorization succeeds.

## Example token issuance
```bash
curl -X POST "http://localhost:8000/auth/mock-idp-token?username=nilesh.fde&roles=ops_viewer&roles=fde_admin"
```

## Example protected request
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/incidents
```

## Run it
From the repository root:

```bash
cd day4_oidc_and_rbac
uvicorn rbac_auth_service:app --reload
```

## Best use cases
- API gateway authorization demos
- JWT validation exercises
- Role-based access control examples
- Internal service security onboarding and training

## Notes
This folder is intentionally minimal and not a full enterprise identity provider. It is meant to teach the core pattern behind OIDC-style token validation and RBAC gatekeeping in a fast, demo-friendly implementation.
