import json
import re

from sqlalchemy.orm import Session

from app.services.ai.ai_gateway import AIGateway
from app.services.ai.entity_extractor import EntityExtractor
from app.services.ai.intent_detector import IntentDetector
from app.services.ai.response_generator import ResponseGenerator
from app.services.rag.retrieval_service import RetrievalService
from app.services.tools import register_builtin_tools
from app.services.tools.tool_registry import tool_registry


class AIOrchestrator:
    def __init__(self):
        register_builtin_tools()
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
        allow_credit_bureau: bool = False,
    ) -> str:
        faq_context = ""
        if db is not None:
            faq_context = RetrievalService(db).build_context(text, limit=3)

        system_content = (
            "Eres CrediBot, un asistente por WhatsApp claro, amable y profesional. "
            "Responde en espanol, de forma breve y natural. "
            "No inventes datos ni prometas aprobaciones definitivas.\n\n"
            "Tienes acceso a herramientas que puedes usar cuando sea relevante:\n"
            "- listar_productos_credito: para conocer productos vigentes sin inventarlos.\n"
            "- consultar_requisitos_producto: para documentos segun producto y ocupacion.\n"
            "- evaluar_precalificacion: para una simulacion con reglas de la base, sin buro.\n"
            "- calcular_amortizacion: cuando el usuario pregunte por cuotas mensuales, "
            "tablas de pago, intereses, o cuanto pagaria al mes.\n"
            "- consultar_estado_cliente: cuando quiera saber el estado de su solicitud "
            "o historial de creditos.\n"
            "- consultar_historial_crediticio: cuando el usuario entregue una cedula "
            "o telefono y quiera revisar score, deuda, mora o resultado del historial crediticio.\n"
            "- obtener_reglas_credito: cuando pregunte por que fue aprobado o rechazado, "
            "o cuales son las reglas del credito.\n"
            "- consultar_politica: cuando pregunte sobre requisitos, documentos, "
            "plazos, tasas de interes, o terminos y condiciones.\n\n"
            "Nunca uses una tasa escrita por el usuario como tasa oficial ni afirmes que una "
            "simulacion es una aprobacion. No solicites claves, PIN, CVV ni contrasenas.\n\n"
            "Usa estas herramientas cuando el usuario haga preguntas especificas. "
            "No las uses si no es necesario.\n\n"
            "Cuando respondas una consulta del usuario, al final invitalo a seguir "
            "con la precalificacion de credito si aun no la ha completado. "
            "Menciona que puede escribir 'quiero mi credito' o 'empecemos' para iniciar."
        )

        if faq_context:
            system_content += (
                "\n\nContexto FAQ disponible para responder preguntas de politicas, "
                "requisitos o condiciones:\n"
                f"{faq_context}"
            )

        messages: list[dict] = [
            {
                "role": "system",
                "content": system_content,
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

        tools_specs = [
            spec
            for spec in tool_registry.to_openai_specs()
            if allow_credit_bureau
            or spec.get("function", {}).get("name") != "consultar_historial_crediticio"
        ]

        if not tools_specs:
            response = self.gateway.generate_chat(messages=messages, temperature=0.4)

            if response:
                return response

            return (
                "Ahora mismo no puedo generar una respuesta con IA. "
                "Verifica que GROQ_API_KEY este configurada e intenta nuevamente."
            )

        final_text, tool_results = self.gateway.generate_with_tools(
            messages=messages,
            tools=tools_specs,
            tool_choice="auto",
            temperature=0.4,
        )

        if not tool_results:
            inline_tool_call = self._extract_inline_tool_call(final_text)
            if inline_tool_call:
                tool_name, arguments = inline_tool_call
                tool_result = self._execute_tool(tool_name, arguments, db)
                if tool_result is not None:
                    response = self._generate_tool_result_response(
                        messages=messages,
                        tool_name=tool_name,
                        tool_result=tool_result,
                    )
                    if response:
                        return response

        if tool_results:
            for tr in tool_results:
                tool_name = tr.get("tool_name", "")
                parsed_arguments = self._parse_tool_arguments(tr.get("arguments", "{}"))
                if parsed_arguments is None:
                    continue

                result = self._execute_tool(tool_name, parsed_arguments, db)
                if result is None:
                    continue

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr.get("tool_call_id", ""),
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Con base en los resultados de las herramientas que ejecutaste, "
                        "responde al usuario de forma clara y natural en espanol."
                    ),
                }
            )

            final_text = self.gateway.generate_chat(messages=messages, temperature=0.4)

        if final_text:
            return final_text

        return (
            "Ahora mismo no puedo generar una respuesta con IA. "
            "Verifica que GROQ_API_KEY este configurada e intenta nuevamente."
        )

    def _execute_tool(
        self,
        tool_name: str,
        arguments: dict,
        db: Session | None,
    ) -> dict | None:
        tool_def = tool_registry.get(tool_name)
        if not tool_def:
            return None

        if tool_def.requires_db:
            if db is None:
                return {"error": "La herramienta requiere una conexion segura a la base de datos."}
            return tool_def.fn(**arguments, db=db)

        return tool_def.fn(**arguments)

    def _extract_inline_tool_call(self, text: str) -> tuple[str, dict] | None:
        value = (text or "").strip()
        if not value:
            return None

        match = re.search(
            r"<function=([a-zA-Z_][a-zA-Z0-9_]*)>\s*(\{.*?\})\s*</function>",
            value,
            flags=re.DOTALL,
        )
        if not match:
            return None

        arguments = self._parse_tool_arguments(match.group(2))
        if arguments is None:
            return None

        return match.group(1), arguments

    def _parse_tool_arguments(self, raw_arguments: str) -> dict | None:
        try:
            arguments = json.loads(raw_arguments or "{}")
        except (json.JSONDecodeError, TypeError):
            return None

        if not isinstance(arguments, dict):
            return None

        return arguments

    def _generate_tool_result_response(
        self,
        messages: list[dict],
        tool_name: str,
        tool_result: dict,
    ) -> str:
        follow_up_messages = list(messages)
        follow_up_messages.append(
            {
                "role": "user",
                "content": (
                    f"Resultado de la herramienta {tool_name}: "
                    f"{json.dumps(tool_result, ensure_ascii=False)}\n\n"
                    "Responde al usuario de forma clara, natural y breve en espanol. "
                    "No muestres JSON ni etiquetas de herramientas."
                ),
            }
        )

        response = self.gateway.generate_chat(
            messages=follow_up_messages,
            temperature=0.4,
        )
        return (response or "").strip()

    def get_model_name(self) -> str:
        return self.gateway.get_model_name()
