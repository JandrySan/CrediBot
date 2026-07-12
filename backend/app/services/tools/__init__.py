from app.services.tools.base import Tool
from app.services.tools.registry import ToolRegistry
from app.services.tools.executor import ToolExecutor

tool_registry = ToolRegistry()

from app.services.tools.credit_tools import CheckCreditRulesTool, CalculatePaymentTool
from app.services.tools.communication_tools import HandoffToAgentTool

tool_registry.register(CheckCreditRulesTool())
tool_registry.register(CalculatePaymentTool())
tool_registry.register(HandoffToAgentTool())

__all__ = [
    "Tool",
    "ToolRegistry",
    "ToolExecutor",
    "tool_registry",
]
