from app.services.ai.groq_service import GroqService


class ResponseService:
    def __init__(self):
        self.groq = GroqService()

    def humanize(self, message: str) -> str:
        system_prompt = """
        Eres CrediBot, un asistente financiero amable y claro.
        Reescribe el mensaje manteniendo el significado.
        No prometas aprobación definitiva.
        Usa un tono profesional, breve y cercano.
        """

        user_prompt = f"""
        Mensaje base:
        {message}
        """

        response = self.groq.generate_text(system_prompt, user_prompt)

        if not response:
            return message

        return response