import json
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.services.tools.tool_registry import tool_registry


class ToolExecutionError(Exception):
    pass


class ToolExecutor:
    def __init__(self, db: Session | None = None):
        self.db = db

    def execute_tool_call(self, tool_call: Any) -> dict[str, Any]:
        function_data = tool_call.function
        tool_name = function_data.name

        tool_def = tool_registry.get(tool_name)
        if not tool_def:
            return {
                "tool_name": tool_name,
                "success": False,
                "error": f"Tool '{tool_name}' no esta registrada",
            }

        try:
            arguments = json.loads(function_data.arguments)
        except (json.JSONDecodeError, TypeError):
            return {
                "tool_name": tool_name,
                "success": False,
                "error": f"Argumentos invalidos para tool '{tool_name}'",
            }

        try:
            if tool_def.requires_db and self.db is not None:
                result = tool_def.fn(**arguments, db=self.db)
            else:
                result = tool_def.fn(**arguments)

            return {
                "tool_name": tool_name,
                "success": True,
                "result": result,
            }

        except (ArithmeticError, SQLAlchemyError, TypeError, ValueError) as exc:
            return {
                "tool_name": tool_name,
                "success": False,
                "error": str(exc),
            }

    def execute_tool_calls(self, tool_calls: list[Any]) -> list[dict[str, Any]]:
        return [self.execute_tool_call(tc) for tc in tool_calls]
