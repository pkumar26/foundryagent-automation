"""Shared tool utilities for all agents."""

import inspect
from typing import Callable, get_type_hints

from azure.ai.projects.models import FunctionTool

_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def create_function_tool(func: Callable, description: str | None = None) -> FunctionTool:
    """Create a FunctionTool from a Python function using JSON schema.

    Inspects the function's signature and docstring to build a JSON schema
    for the parameters.

    Args:
        func: The Python function to wrap as a tool.
        description: Optional description override (defaults to first line of docstring).

    Returns:
        A FunctionTool instance with JSON schema parameters.
    """
    name = func.__name__

    # Extract description from docstring if not provided
    if description is None:
        doc = inspect.getdoc(func) or ""
        description = doc.split("\n")[0].strip() if doc else name

    # Build JSON schema from signature
    sig = inspect.signature(func)
    hints = get_type_hints(func)
    properties: dict = {}
    required: list[str] = []

    # Parse docstring for parameter descriptions
    param_docs = _parse_param_docs(func)

    for param_name, param in sig.parameters.items():
        python_type = hints.get(param_name, str)
        json_type = _TYPE_MAP.get(python_type, "string")
        prop: dict = {"type": json_type}
        if param_name in param_docs:
            prop["description"] = param_docs[param_name]
        properties[param_name] = prop
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    schema = {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }

    return FunctionTool(
        name=name,
        parameters=schema,
        description=description,
        strict=True,
    )


def _parse_param_docs(func: Callable) -> dict[str, str]:
    """Extract parameter descriptions from Google-style docstrings."""
    doc = inspect.getdoc(func) or ""
    param_docs: dict[str, str] = {}
    in_args = False
    for line in doc.split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if in_args:
            if stripped.lower().startswith(("returns:", "raises:", "yields:")):
                break
            if ":" in stripped and not stripped.startswith(" "):
                param_part, desc_part = stripped.split(":", 1)
                param_name = param_part.strip()
                param_docs[param_name] = desc_part.strip()
    return param_docs
