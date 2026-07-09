from app.services.ai.intent_detector import IntentDetector
from app.services.ai.entity_extractor import EntityExtractor
from app.services.ai.response_generator import ResponseGenerator
from app.services.ai.ai_gateway import AIGateway


class AIOrchestrator:
    def __init__(self):
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        self.gateway = AIGateway()

    def analyze_message(self, text: str) -> dict:
        intent = self.intent_detector.detect(text)
        entities = self.entity_extractor.extract_credit_entities(text)

        return {
            "intent": intent,
            **entities,
        }

    def improve_response(self, message: str) -> str:
        return self.response_generator.generate(message)

    def generate_whatsapp_reply(self, text: str, history: list[dict] | None = None) -> str:
        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "Eres CrediBot, un asistente por WhatsApp claro, amable y profesional. "
                    "Responde en espanol, de forma breve y natural. "
                    "No inventes datos ni prometas aprobaciones definitivas."
                ),
            }
        ]

        for item in history or []:
            role = item.get("role")
            content = (item.get("content") or "").strip()

            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

        user_text = (text or "").strip()
        if not user_text:
            return "Te leo. Escribe tu mensaje para poder ayudarte."

        messages.append({"role": "user", "content": user_text})

        response = self.gateway.generate_chat(messages=messages, temperature=0.4)

        if response:
            return response

        return (
            "Ahora mismo no puedo generar una respuesta con IA. "
            "Verifica que GROQ_API_KEY este configurada e intenta nuevamente."
        )

    def get_model_name(self) -> str:
        return self.gateway.get_model_name()
