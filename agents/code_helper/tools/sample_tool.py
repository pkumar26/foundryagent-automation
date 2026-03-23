"""Sample greeting tool for the code-helper agent."""

from agents._base.tools import create_function_tool


def greet_user(name: str) -> str:
    """Greet a user by name.

    Args:
        name: The name of the user to greet.

    Returns:
        A personalised greeting message.
    """
    return f"Hello, {name}! I'm the Code Helper agent. How can I assist you today?"


# Exported tools list — consumed by agent_factory via TOOLS
TOOLS = [create_function_tool(greet_user)]
