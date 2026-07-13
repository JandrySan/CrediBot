from app.services.ai.ai_orchestrator import AIOrchestrator


def test_extract_inline_tool_call_from_groq_text_response():
    orchestrator = AIOrchestrator.__new__(AIOrchestrator)

    tool_call = orchestrator._extract_inline_tool_call(
        '<function=consultar_politica>{"consulta":"requisitos"}</function>'
    )

    assert tool_call == ("consultar_politica", {"consulta": "requisitos"})


def test_extract_inline_tool_call_ignores_regular_text():
    orchestrator = AIOrchestrator.__new__(AIOrchestrator)

    assert orchestrator._extract_inline_tool_call("Hola, puedo ayudarte.") is None
