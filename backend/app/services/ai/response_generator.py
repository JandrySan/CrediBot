from app.services.ai.ai_gateway import AIGateway


class ResponseGenerator:
    def __init__(self):
        self.ai = AIGateway()

    def generate(
        self,
        base_message: str,
        last_user_message: str = "",
        faq_context: str = "",
    ) -> str:
        system_prompt = """
        Eres CrediBot, un asistente financiero amable, claro y profesional por WhatsApp.
        Reescribe el mensaje manteniendo exactamente el mismo significado y los mismos datos.
        Reglas obligatorias:
        - No inventes beneficios ni datos nuevos.
        - No prometas aprobacion definitiva.
        - No empieces con "de nada", "con gusto" o "a la orden" salvo que el usuario haya agradecido.
        - Integra la informacion de forma conversacional, no como lista separada de datos.
        - Si hablas de plazo, usa la forma "X meses".
        - Responde breve, natural y coherente con lo ultimo que dijo el usuario.
        - Si se incluye contexto FAQ, usalo solo para explicar politicas, requisitos o condiciones.
        Devuelve solo el mensaje final.
        """

        user_prompt = f"""
        Ultimo mensaje del usuario:
        {last_user_message or "(sin contexto adicional)"}

        Contexto FAQ:
        {faq_context or "(sin contexto FAQ)"}

        Mensaje base:
        {base_message}
        """

        response = self.ai.generate_text(system_prompt, user_prompt)

        return response if response else base_message
