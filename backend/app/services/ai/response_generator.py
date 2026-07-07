from app.services.ai.ai_gateway import AIGateway


class ResponseGenerator:
    def __init__(self):
        self.ai = AIGateway()

    def generate(self, base_message: str) -> str:
        system_prompt = """
        Eres CrediBot, un asistente financiero amable, claro y profesional.
        Reescribe el mensaje manteniendo exactamente el mismo significado.
        No inventes beneficios.
        No prometas aprobación definitiva.
        La respuesta debe ser breve.
        """

        user_prompt = f"""
        Mensaje base:
        {base_message}
        """

        response = self.ai.generate_text(system_prompt, user_prompt)

        return response if response else base_message