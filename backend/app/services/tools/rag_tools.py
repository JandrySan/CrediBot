from app.services.tools.base import Tool


class SearchFAQTool(Tool):
    def __init__(self, knowledge_base):
        self._kb = knowledge_base

    @property
    def name(self) -> str:
        return "search_faqs"

    @property
    def description(self) -> str:
        return (
            "Busca en la base de conocimiento de FAQs sobre créditos, "
            "tasas de interés, requisitos, documentación, plazos y políticas. "
            "Úsala cuando el usuario haga preguntas sobre productos financieros, "
            "términos, condiciones o cualquier información general de créditos."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La pregunta o consulta del usuario sobre créditos o productos financieros",
                },
            },
            "required": ["query"],
        }

    def run(self, **kwargs) -> dict:
        query = kwargs.get("query", "")
        if not query:
            return {"found": False, "answer": ""}
        context = self._kb.query(query)
        if not context:
            return {"found": False, "answer": ""}
        return {"found": True, "answer": context}
