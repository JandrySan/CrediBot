import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config.settings import settings

ALGORITHM = "HS256"
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class DashboardPrincipal:
    username: str
    role: str


def authenticate_dashboard_user(username: str, password: str) -> DashboardPrincipal | None:
    candidates = (
        (
            settings.DASHBOARD_ADMIN_USERNAME,
            settings.DASHBOARD_ADMIN_PASSWORD,
            "admin",
        ),
        (
            settings.DASHBOARD_ADVISOR_USERNAME,
            settings.DASHBOARD_ADVISOR_PASSWORD,
            "advisor",
        ),
    )
    for configured_user, configured_password, role in candidates:
        if not configured_user or not configured_password:
            continue
        if secrets.compare_digest(username, configured_user) and secrets.compare_digest(
            password,
            configured_password,
        ):
            return DashboardPrincipal(username=configured_user, role=role)
    return None


def create_access_token(principal: DashboardPrincipal) -> str:
    _ensure_auth_configured()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.DASHBOARD_ACCESS_TOKEN_MINUTES)
    return jwt.encode(
        {
            "sub": principal.username,
            "role": principal.role,
            "exp": expires_at,
        },
        settings.DASHBOARD_JWT_SECRET,
        algorithm=ALGORITHM,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> DashboardPrincipal:
    if not settings.DASHBOARD_AUTH_ENABLED:
        return DashboardPrincipal(username="local", role="admin")

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    return decode_access_token(credentials.credentials)


def decode_access_token(token: str) -> DashboardPrincipal:
    _ensure_auth_configured()
    try:
        payload = jwt.decode(
            token,
            settings.DASHBOARD_JWT_SECRET,
            algorithms=[ALGORITHM],
        )
        username = str(payload.get("sub") or "")
        role = str(payload.get("role") or "")
    except JWTError as exc:
        raise _unauthorized() from exc

    if not username or role not in {"admin", "advisor"}:
        raise _unauthorized()
    return DashboardPrincipal(username=username, role=role)


def require_roles(*allowed_roles: str):
    def dependency(
        principal: DashboardPrincipal = Depends(get_current_user),
    ) -> DashboardPrincipal:
        if principal.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para esta operacion.",
            )
        return principal

    return dependency


def _ensure_auth_configured() -> None:
    if not settings.DASHBOARD_JWT_SECRET or not settings.DASHBOARD_ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La autenticacion del dashboard no esta configurada.",
        )


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas o token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
