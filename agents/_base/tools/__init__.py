"""Shared tool utilities for all agents."""

from azure.ai.agents.models import FunctionTool


def create_function_tool(functions: list) -> FunctionTool:
    """Create a FunctionTool from a list of callable functions.

    Args:
        functions: List of Python functions to register as agent tools.

    Returns:
        A FunctionTool instance with the given functions.
    """
    return FunctionTool(functions=functions)
