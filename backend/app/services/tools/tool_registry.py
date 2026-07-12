from typing import Any, Callable

ToolFunc = Callable[..., dict[str, Any]]


class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        fn: ToolFunc,
        requires_db: bool = False,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.fn = fn
        self.requires_db = requires_db

    def to_openai_spec(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def execute(self, **kwargs) -> dict[str, Any]:
        return self.fn(**kwargs)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def to_openai_specs(self) -> list[dict[str, Any]]:
        return [t.to_openai_spec() for t in self._tools.values()]

    def get_required_db_tools(self) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.requires_db]


tool_registry = ToolRegistry()


def tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    requires_db: bool = False,
):
    def decorator(fn: ToolFunc) -> ToolFunc:
        definition = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            fn=fn,
            requires_db=requires_db,
        )
        tool_registry.register(definition)
        return fn

    return decorator
