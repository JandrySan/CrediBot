from app.services.ai.intent_detector import IntentDetector
from app.services.ai.entity_extractor import EntityExtractor
from app.services.ai.response_generator import ResponseGenerator
from app.services.ai.ai_gateway import AIGateway
from app.services.tools.tool_registry import tool_registry
from app.services.tools.tool_executor import ToolExecutor

from sqlalchemy.orm import Session


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

    def improve_response(self, message: str, last_user_message: str = "") -> str:
        return self.response_generator.generate(
            base_message=message,
            last_user_message=last_user_message,
        )

    def generate_whatsapp_reply(
        self,
        text: str,
        history: list[dict] | None = None,
        db: Session | None = None,
    ) -> str:
        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "Eres CrediBot, un asistente por WhatsApp claro, amable y profesional. "
                    "Responde en espanol, de forma breve y natural. "
                    "No inventes datos ni prometas aprobaciones definitivas.\n\n"
                    "Tienes acceso a herramientas que puedes usar cuando sea relevante:\n"
                    "- calcular_amortizacion: cuando el usuario pregunte por cuotas mensuales, "
                    "tablas de pago, intereses, o cuanto pagaria al mes.\n"
                    "- consultar_estado_cliente: cuando quiera saber el estado de su solicitud "
                    "o historial de creditos.\n"
                    "- obtener_reglas_credito: cuando pregunte por que fue aprobado o rechazado, "
                    "o cuales son las reglas del credito.\n"
                    "- consultar_politica: cuando pregunte sobre requisitos, documentos, "
                    "plazos, tasas de interes, o terminos y condiciones.\n\n"
                    "Usa estas herramientas cuando el usuario haga preguntas especificas. "
                    "No las uses si no es necesario."
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

        tools_specs = tool_registry.to_openai_specs()

        if not tools_specs:
            response = self.gateway.generate_chat(messages=messages, temperature=0.4)

            if response:
                return response

            return (
                "Ahora mismo no puedo generar una respuesta con IA. "
                "Verifica que GROQ_API_KEY este configurada e intenta nuevamente."
            )

        executor = ToolExecutor(db=db)
        final_text, tool_results = self.gateway.generate_with_tools(
            messages=messages,
            tools=tools_specs,
            tool_choice="auto",
            temperature=0.4,
        )

        if tool_results:
            for tr in tool_results:
                tool_name = tr.get("tool_name", "")
                tool_def = tool_registry.get(tool_name)
                if not tool_def:
                    continue

                try:
                    import json
                    arguments = json.loads(tr.get("arguments", "{}"))
                except (json.JSONDecodeError, TypeError):
                    continue

                if tool_def.requires_db and db is not None:
                    result = tool_def.fn(**arguments, db=db)
                else:
                    result = tool_def.fn(**arguments)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tr.get("tool_call_id", ""),
                    "content": json.dumps(result, ensure_ascii=False),
                })

            messages.append({
                "role": "user",
                "content": (
                    "Con base en los resultados de las herramientas que ejecutaste, "
                    "responde al usuario de forma clara y natural en espanol."
                ),
            })

            final_text = self.gateway.generate_chat(messages=messages, temperature=0.4)

        if final_text:
            return final_text

        return (
            "Ahora mismo no puedo generar una respuesta con IA. "
            "Verifica que GROQ_API_KEY este configurada e intenta nuevamente."
        )

    def get_model_name(self) -> str:
        return self.gateway.get_model_name()
