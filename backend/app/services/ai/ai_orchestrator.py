from app.services.ai.intent_detector import IntentDetector
from app.services.ai.entity_extractor import EntityExtractor
from app.services.ai.response_generator import ResponseGenerator
from app.services.ai.ai_gateway import AIGateway
from app.services.tools.registry import ToolRegistry
from app.services.tools.executor import ToolExecutor


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

    def process_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: list[dict] | None = None,
        registry: ToolRegistry | None = None,
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-10:])
        messages.append({"role": "user", "content": user_message})

        if registry:
            executor = ToolExecutor(self.gateway, registry)
            return executor.execute(
                system_prompt=system_prompt,
                messages=messages,
                available_tools=registry.get_all(),
            )

        response = self.gateway.chat(messages=messages)
        return response.choices[0].message.content or ""
