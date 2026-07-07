from app.services.ai.extraction_service import ExtractionService
from app.services.ai.response_service import ResponseService


class AIOrchestrator:
    def __init__(self):
        self.extractor = ExtractionService()
        self.response_service = ResponseService()

    def analyze_message(self, text: str) -> dict:
        data = self.extractor.extract_credit_data(text)

        if not data.get("intent"):
            data["intent"] = self._basic_intent_detection(text)

        return data

    def improve_response(self, message: str) -> str:
        return self.response_service.humanize(message)

    def _basic_intent_detection(self, text: str) -> str:
        normalized = text.lower()

        if any(word in normalized for word in ["asesor", "humano", "persona", "agente"]):
            return "asesor"

        if any(word in normalized for word in ["credito", "crédito", "prestamo", "préstamo", "dinero"]):
            return "credito"

        if any(word in normalized for word in ["hola", "buenas", "buenos días", "buenas tardes"]):
            return "saludo"

        return "desconocido"