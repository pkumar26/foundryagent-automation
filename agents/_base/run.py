"""Conversation-and-response lifecycle helper for agent interactions."""

import importlib
import json
import logging

from agents._base.client import get_project_client

logger = logging.getLogger(__name__)

MAX_FUNCTION_CALL_ITERATIONS = 50


class AgentRunError(Exception):
    """Raised when an agent run ends in a non-completed terminal state."""


def run_agent(
    endpoint: str,
    agent_name: str,
    prompt: str,
) -> str:
    """Execute a single-turn conversation with a deployed agent.

    Creates a conversation, sends a message, processes the agent response
    (including any function calls), and returns the response text.

    Args:
        endpoint: Azure AI Project endpoint URL.
        agent_name: The agent name (used in agent_reference and tool lookup).
        prompt: The user message to send.

    Returns:
        The agent's response text.

    Raises:
        AgentRunError: If the response indicates failure.
    """
    project_client = get_project_client(endpoint)
    tool_functions = _load_tool_functions(agent_name)

    with project_client.get_openai_client() as openai_client:
        # Create conversation with initial message
        conversation = openai_client.conversations.create(
            items=[{"type": "message", "role": "user", "content": prompt}],
        )
        logger.info("Created conversation %s for agent %s", conversation.id, agent_name)

        try:
            agent_ref = {
                "agent_reference": {"name": agent_name, "type": "agent_reference"},
            }

            # Get initial response
            response = openai_client.responses.create(
                conversation=conversation.id,
                extra_body=agent_ref,
            )

            # Handle function calls in a loop
            response = _handle_function_calls(
                openai_client,
                conversation.id,
                agent_ref,
                response,
                tool_functions,
            )

            return response.output_text or ""
        finally:
            try:
                openai_client.conversations.delete(conversation_id=conversation.id)
            except Exception:
                logger.warning("Failed to delete conversation %s", conversation.id)


def _handle_function_calls(openai_client, conversation_id, agent_ref, response, tool_functions):
    """Process function_call items in the response until none remain."""
    for _ in range(MAX_FUNCTION_CALL_ITERATIONS):
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response

        results = []
        for call in calls:
            func = tool_functions.get(call.name)
            if func is None:
                logger.error("Unknown tool function: %s", call.name)
                results.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps({"error": f"Unknown function: {call.name}"}),
                    }
                )
                continue

            try:
                arguments = json.loads(call.arguments) if call.arguments else {}
                result = func(**arguments)
                results.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(result) if not isinstance(result, str) else result,
                    }
                )
            except Exception as exc:
                logger.exception("Tool %s raised an error", call.name)
                results.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps({"error": str(exc)}),
                    }
                )

        response = openai_client.responses.create(
            conversation=conversation_id,
            extra_body=agent_ref,
            input=results,
        )

    raise AgentRunError(
        f"Maximum iterations ({MAX_FUNCTION_CALL_ITERATIONS}) exceeded for function calls. "
        "The agent may be stuck in a loop."
    )


def _load_tool_functions(agent_name: str) -> dict:
    """Load tool functions from an agent's tools module.

    Returns a dict mapping function name → callable.
    """
    module_name = agent_name.replace("-", "_")
    try:
        tools_module = importlib.import_module(f"agents.{module_name}.tools")
    except ModuleNotFoundError:
        return {}
    functions = {}
    for tool in getattr(tools_module, "TOOLS", []):
        func = getattr(tools_module, tool.name, None)
        if func is None:
            # Check sub-modules (e.g., sample_tool)
            for attr_name in dir(tools_module):
                sub = getattr(tools_module, attr_name)
                if hasattr(sub, tool.name):
                    func = getattr(sub, tool.name)
                    break
        if func and callable(func):
            functions[tool.name] = func
    return functions
