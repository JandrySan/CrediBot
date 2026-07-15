from fastapi import APIRouter, Depends, HTTPException, status

from app.config.settings import settings
from app.schemas.auth import AuthConfigResponse, LoginRequest, TokenResponse
from app.security.auth import authenticate_dashboard_user, create_access_token
from app.security.rate_limit import rate_limit

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/config", response_model=AuthConfigResponse)
def get_auth_config() -> AuthConfigResponse:
    return AuthConfigResponse(enabled=settings.DASHBOARD_AUTH_ENABLED)


@router.post(
    "/token",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit("dashboard-login", settings.LOGIN_RATE_LIMIT_PER_MINUTE))],
)
def login(credentials: LoginRequest) -> TokenResponse:
    principal = authenticate_dashboard_user(
        credentials.username,
        credentials.password,
    )
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contrasena incorrectos.",
        )
    return TokenResponse(
        access_token=create_access_token(principal),
        role=principal.role,
    )
