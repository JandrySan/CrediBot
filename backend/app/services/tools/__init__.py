def register_builtin_tools() -> None:
    """Import the built-in tool modules so their decorators register them."""
    from app.services.tools import (
        credit_bureau_tools,
        customer_tools,
        financial_tools,
        policy_tools,
    )

    _ = (credit_bureau_tools, customer_tools, financial_tools, policy_tools)
