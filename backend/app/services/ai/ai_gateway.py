import json
from typing import Any

from groq import Groq

from app.config.settings import settings


class AIGateway:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = "llama-3.1-8b-instant"

    def is_available(self) -> bool:
        return self.client is not None

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.client:
            return {}

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            return json.loads(response.choices[0].message.content)

        except Exception:
            return {}

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            return ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )

            return response.choices[0].message.content.strip()

        except Exception:
            return ""

    def generate_chat(self, messages: list[dict], temperature: float = 0.4) -> str:
        if not self.client:
            return ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )

            return response.choices[0].message.content.strip()

        except Exception:
            return ""

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict[str, Any]],
        tool_choice: str = "auto",
        temperature: float = 0.4,
        max_tool_rounds: int = 5,
    ) -> tuple[str, list[dict[str, Any]]]:
        if not self.client:
            return "", []

        current_messages = list(messages)
        all_tool_results: list[dict[str, Any]] = []
        rounds = 0

        while rounds < max_tool_rounds:
            rounds += 1

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=current_messages,
                    temperature=temperature,
                    tools=tools,
                    tool_choice=tool_choice,
                )
            except Exception:
                break

            choice = response.choices[0]
            message = choice.message

            if not message.tool_calls:
                final_text = (message.content or "").strip()
                return final_text, all_tool_results

            assistant_msg = {"role": "assistant", "content": message.content or ""}
            if hasattr(message, "tool_calls") and message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]

            current_messages.append(assistant_msg)

            for tc in message.tool_calls:
                tool_result = {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": "",
                }
                current_messages.append(tool_result)
                all_tool_results.append({
                    "tool_name": tc.function.name,
                    "tool_call_id": tc.id,
                    "arguments": tc.function.arguments,
                })

        final_text = ""
        if current_messages and current_messages[-1].get("role") == "assistant":
            final_text = (current_messages[-1].get("content") or "").strip()

        return final_text, all_tool_results

    def get_model_name(self) -> str:
        return self.model
