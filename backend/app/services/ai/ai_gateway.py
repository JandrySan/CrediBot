import json
from groq import Groq

from app.config.settings import settings


class AIGateway:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = "llama-3.1-8b-instant"

    def is_available(self) -> bool:
        return self.client is not None

    def chat(self, messages: list[dict], tools: list[dict] | None = None,
             tool_choice: str | None = None, temperature: float = 0.3):
        if not self.client:
            raise RuntimeError("AIGateway: Groq client not configured")

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        return self.client.chat.completions.create(**kwargs)

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.client:
            return {}
        try:
            response = self.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {}

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            return ""
        try:
            response = self.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return ""

    def get_model_name(self) -> str:
        return self.model
