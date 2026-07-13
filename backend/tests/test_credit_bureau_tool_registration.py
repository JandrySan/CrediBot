from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.tools.tool_registry import tool_registry


def test_credit_bureau_tool_is_registered_for_ai():
    AIOrchestrator()

    tool = tool_registry.get("consultar_historial_crediticio")

    assert tool is not None
    assert tool.requires_db is True
    assert tool.to_openai_spec()["function"]["name"] == "consultar_historial_crediticio"
