from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.services.whatsapp import twilio_service
from app.services.whatsapp.templates import (
    TransactionalTemplateKey,
    get_transactional_template,
    render_transactional_template,
    twilio_content_variables,
)


def _settings(content_sids: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        TWILIO_ENABLED=True,
        TWILIO_ACCOUNT_SID="AC0000000000000000000000000000000",
        TWILIO_AUTH_TOKEN="test-auth-token",
        TWILIO_WHATSAPP_FROM="+14155238886",
        TWILIO_WEBHOOK_URL="",
        TWILIO_CONTENT_TEMPLATE_SIDS=content_sids,
    )


def test_catalog_exposes_versioned_transactional_contract():
    template = get_transactional_template(TransactionalTemplateKey.ADVISOR_ASSIGNED)

    assert template.version == "1.0"
    assert template.variables == ("advisor_name",)


def test_template_renderer_requires_exact_non_empty_variables():
    with pytest.raises(ValueError, match="Faltan variables"):
        render_transactional_template(TransactionalTemplateKey.ADVISOR_ASSIGNED)

    with pytest.raises(ValueError, match="no esperadas"):
        render_transactional_template(
            TransactionalTemplateKey.HANDOFF_REQUESTED,
            {"extra": "dato"},
        )

    with pytest.raises(ValueError, match="no pueden estar vacías"):
        render_transactional_template(
            TransactionalTemplateKey.ADVISOR_ASSIGNED,
            {"advisor_name": "   "},
        )


def test_template_renders_sandbox_text_and_twilio_position_variables():
    variables = {"advisor_name": "Ana, asesora de CrediBot"}

    rendered = render_transactional_template(
        TransactionalTemplateKey.ADVISOR_ASSIGNED,
        variables,
    )

    assert rendered.startswith("Ana, asesora de CrediBot tomó")
    assert twilio_content_variables(
        TransactionalTemplateKey.ADVISOR_ASSIGNED,
        variables,
    ) == {"1": "Ana, asesora de CrediBot"}


def test_send_template_uses_text_fallback_in_sandbox():
    with patch.object(twilio_service, "settings", _settings()):
        service = twilio_service.TwilioWhatsAppService()
        service.client = Mock()
        service.client.messages.create.return_value.sid = "SM-TEXT"

        result = service.send_template(
            to="593999999999",
            template_key=TransactionalTemplateKey.HANDOFF_REQUESTED,
        )

    payload = service.client.messages.create.call_args.kwargs
    assert result["success"] is True
    assert result["template_transport"] == "sandbox_text"
    assert "envié tu conversación" in payload["body"]
    assert "content_sid" not in payload


def test_send_template_uses_content_sid_when_configured():
    content_sids = '{"advisor_assigned":"HX00000000000000000000000000000000"}'
    with patch.object(twilio_service, "settings", _settings(content_sids)):
        service = twilio_service.TwilioWhatsAppService()
        service.client = Mock()
        service.client.messages.create.return_value.sid = "SM-CONTENT"

        result = service.send_template(
            to="593999999999",
            template_key=TransactionalTemplateKey.ADVISOR_ASSIGNED,
            variables={"advisor_name": "Un asesor humano"},
        )

    payload = service.client.messages.create.call_args.kwargs
    assert result["success"] is True
    assert result["template_transport"] == "content_sid"
    assert payload["content_sid"].startswith("HX")
    assert payload["content_variables"] == '{"1": "Un asesor humano"}'
    assert "body" not in payload
