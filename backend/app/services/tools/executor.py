import json
from typing import Any

from app.services.tools.base import Tool
from app.services.tools.registry import ToolRegistry
from app.services.ai.ai_gateway import AIGateway


class ToolExecutionError(Exception):
    ...


class ToolExecutor:
    def __init__(self, gateway: AIGateway, registry: ToolRegistry):
        self.gateway = gateway
        self.registry = registry

    def execute(
        self,
        system_prompt: str,
        messages: list[dict],
        available_tools: list[Tool] | None = None,
        max_rounds: int = 5,
    ) -> str:
        tools = available_tools or self.registry.get_all()
        tool_defs = [t.to_definition() for t in tools]

        for _ in range(max_rounds):
            response = self.gateway.chat(
                messages=messages,
                tools=tool_defs,
                tool_choice="auto",
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or ""

            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tool_call in msg.tool_calls:
                tool = self.registry.get(tool_call.function.name)
                if not tool:
                    result = {"error": f"Tool '{tool_call.function.name}' not found"}
                else:
                    try:
                        args = json.loads(tool_call.function.arguments)
                        raw = tool.run(**args)
                        result = {"success": True, "data": raw}
                    except Exception as e:
                        result = {"error": str(e)}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                })

        return messages[-1].get("content", "")
