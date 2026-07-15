import asyncio
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from twilio.request_validator import RequestValidator

from app.config.settings import settings
from app.security.auth import (
    DashboardPrincipal,
    authenticate_dashboard_user,
    create_access_token,
    decode_access_token,
)
from app.security.rate_limit import InMemoryRateLimiter
from app.security.twilio_signature import validate_twilio_signature


def test_dashboard_authentication_and_token_roundtrip(monkeypatch):
    monkeypatch.setattr(settings, "DASHBOARD_ADMIN_USERNAME", "operator")
    monkeypatch.setattr(settings, "DASHBOARD_ADMIN_PASSWORD", "secret-password")
    monkeypatch.setattr(settings, "DASHBOARD_JWT_SECRET", "test-signing-secret")

    principal = authenticate_dashboard_user("operator", "secret-password")

    assert principal == DashboardPrincipal(username="operator", role="admin")
    assert decode_access_token(create_access_token(principal)) == principal
    assert authenticate_dashboard_user("operator", "incorrect") is None


def test_rate_limiter_rejects_requests_over_the_limit():
    rate_limiter = InMemoryRateLimiter()
    rate_limiter.check("login:127.0.0.1", limit=1)

    with pytest.raises(HTTPException) as error:
        rate_limiter.check("login:127.0.0.1", limit=1)

    assert error.value.status_code == 429


def test_twilio_signature_is_validated(monkeypatch):
    url = "https://example.test/webhook/whatsapp"
    params = {"From": "whatsapp:+593000000000", "Body": "hola"}
    auth_token = "twilio-test-token"
    signature = RequestValidator(auth_token).compute_signature(url, params)
    body = urlencode(params).encode()

    monkeypatch.setattr(settings, "TWILIO_ENABLED", True)
    monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", True)
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", auth_token)
    monkeypatch.setattr(settings, "TWILIO_WEBHOOK_URL", url)

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "https",
            "server": ("example.test", 443),
            "path": "/webhook/whatsapp",
            "query_string": b"",
            "headers": [
                (b"content-type", b"application/x-www-form-urlencoded"),
                (b"x-twilio-signature", signature.encode()),
            ],
        },
        receive,
    )

    asyncio.run(validate_twilio_signature(request))
