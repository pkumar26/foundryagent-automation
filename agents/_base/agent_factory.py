"""Shared agent factory — create or idempotently update agents in Azure AI Foundry."""

import importlib
import logging
from pathlib import Path

from azure.ai.agents.models import Agent

from agents._base.client import get_client
from agents._base.config import FoundryBaseConfig

logger = logging.getLogger(__name__)


def create_or_update_agent(config: FoundryBaseConfig) -> Agent:
    """Create a new agent or update an existing one idempotently.

    Steps:
    1. Load instructions from config.agent_instructions_path
    2. Collect tools from the agent's tools/ module
    3. Conditionally append knowledge tool (if KNOWLEDGE_SOURCE_ENABLED)
    4. Conditionally append GitHub MCP tool (if GITHUB_MCP_ENABLED)
    5. List existing agents, find by name
    6. If found: update_agent() with new instructions, model, tools
    7. If not found: create_agent() with all parameters
    8. Return the Agent object

    Args:
        config: An agent-specific config object (subclass of FoundryBaseConfig).

    Returns:
        The created or updated Agent object from the SDK.

    Raises:
        FileNotFoundError: If the instructions file does not exist.
        ValueError: If the instructions file is empty.
    """
    # 1. Load instructions
    instructions_path = Path(config.agent_instructions_path)
    if not instructions_path.exists():
        raise FileNotFoundError(f"Instructions file not found: {instructions_path}")
    instructions = instructions_path.read_text(encoding="utf-8").strip()
    if not instructions:
        raise ValueError(f"Instructions file is empty: {instructions_path}")

    # 2. Collect tools from agent's tools module
    tools = _collect_agent_tools(config)

    # 3-4. Conditionally append integration tools
    tools = _append_integration_tools(config, tools)

    # 5. Get client and list existing agents
    client = get_client(config.foundry_project_connection_string)

    existing_agent = _find_agent_by_name(client, config.agent_name)

    # 6-7. Create or update
    tool_definitions = []
    for tool in tools:
        tool_definitions.extend(tool.definitions)

    if existing_agent:
        agent = client.update_agent(
            agent_id=existing_agent.id,
            model=config.agent_model,
            name=config.agent_name,
            instructions=instructions,
            tools=tool_definitions,
        )
        logger.info("Updated agent '%s' (id: %s)", config.agent_name, agent.id)
    else:
        agent = client.create_agent(
            model=config.agent_model,
            name=config.agent_name,
            instructions=instructions,
            tools=tool_definitions,
        )
        logger.info("Created agent '%s' (id: %s)", config.agent_name, agent.id)

    return agent


def _find_agent_by_name(client, name: str):
    """Find an existing agent by name, or return None."""
    for agent in client.list_agents():
        if agent.name == name:
            return agent
    return None


def _collect_agent_tools(config: FoundryBaseConfig) -> list:
    """Collect FunctionTool instances from the agent's tools module."""
    # Derive the agent module path from the agent_name
    # e.g., "code-helper" → "agents.code_helper.tools"
    module_name = config.agent_name.replace("-", "_")
    tools_module_path = f"agents.{module_name}.tools"

    try:
        tools_module = importlib.import_module(tools_module_path)
    except ModuleNotFoundError:
        return []

    tools = []
    if hasattr(tools_module, "TOOLS"):
        tools.extend(tools_module.TOOLS)
    return tools


def _append_integration_tools(config: FoundryBaseConfig, tools: list) -> list:
    """Conditionally append integration tools based on feature flags."""
    module_name = config.agent_name.replace("-", "_")

    # Knowledge source integration
    if getattr(config, "knowledge_source_enabled", False):
        try:
            knowledge_mod = importlib.import_module(f"agents.{module_name}.integrations.knowledge")
            knowledge_tool = knowledge_mod.get_knowledge_tool(config)
            if knowledge_tool is not None:
                tools.append(knowledge_tool)
        except (ModuleNotFoundError, AttributeError) as exc:
            logger.warning("Failed to load knowledge integration for %s: %s", module_name, exc)

    # GitHub MCP integration
    if getattr(config, "github_mcp_enabled", False):
        try:
            mcp_mod = importlib.import_module(f"agents.{module_name}.integrations.github_mcp")
            mcp_tool = mcp_mod.get_github_mcp_tool(config)
            if mcp_tool is not None:
                tools.append(mcp_tool)
        except (ModuleNotFoundError, AttributeError) as exc:
            logger.warning("Failed to load GitHub MCP integration for %s: %s", module_name, exc)

    return tools
