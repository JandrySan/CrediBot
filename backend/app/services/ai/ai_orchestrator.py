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

    def get_model_name(self) -> str:
        return self.gateway.get_model_name()