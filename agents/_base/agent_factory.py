"""Shared agent factory — create or idempotently update agents in Azure AI Foundry."""

import importlib
import logging
from pathlib import Path

from azure.ai.projects.models import PromptAgentDefinition

from agents._base.client import get_project_client
from agents._base.config import FoundryBaseConfig

logger = logging.getLogger(__name__)


def create_or_update_agent(config: FoundryBaseConfig):
    """Create or update an agent in Azure AI Foundry.

    Each call creates a new immutable version of the agent. The latest version
    becomes the active one, so re-deploying after a config change (e.g. enabling
    a new tool) will update the agent automatically.

    Args:
        config: An agent-specific config object (subclass of FoundryBaseConfig).

    Returns:
        The agent version object from the SDK with .id, .name, .version properties.

    Raises:
        FileNotFoundError: If the instructions file does not exist.
        ValueError: If the instructions file is empty.
    """
    # 1. Load instructions — resolve relative paths against the project root
    instructions_path = Path(config.agent_instructions_path)
    if not instructions_path.is_absolute():
        project_root = Path(__file__).resolve().parent.parent.parent
        instructions_path = project_root / instructions_path
    if not instructions_path.exists():
        raise FileNotFoundError(f"Instructions file not found: {instructions_path}")
    instructions = instructions_path.read_text(encoding="utf-8").strip()
    if not instructions:
        raise ValueError(f"Instructions file is empty: {instructions_path}")

    # 2. Collect tools from agent's tools module
    tools = _collect_agent_tools(config)

    # 3. Conditionally append integration tools
    tools = _append_integration_tools(config, tools)

    # 4. Get project client and create version
    client = get_project_client(config.azure_ai_project_endpoint)

    definition = PromptAgentDefinition(
        model=config.agent_model,
        instructions=instructions,
        tools=tools,
    )

    agent = client.agents.create_version(
        agent_name=config.agent_name,
        definition=definition,
    )
    logger.info(
        "Created agent version '%s' (id: %s, version: %s)",
        config.agent_name,
        agent.id,
        getattr(agent, "version", "N/A"),
    )

    return agent


def _collect_agent_tools(config: FoundryBaseConfig) -> list:
    """Collect FunctionTool instances from the agent's tools module."""
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

    # Code Interpreter integration
    if getattr(config, "code_interpreter_enabled", False):
        from azure.ai.projects.models import CodeInterpreterTool

        tools.append(CodeInterpreterTool())
        logger.info("Added Code Interpreter tool for %s", module_name)

    # Web Search integration
    if getattr(config, "web_search_enabled", False):
        from azure.ai.projects.models import WebSearchTool

        tools.append(WebSearchTool())
        logger.info("Added Web Search tool for %s", module_name)

    # GitHub MCP integration
    if getattr(config, "github_enabled", False):
        connection_id = getattr(config, "github_project_connection_id", "")
        if not connection_id:
            logger.warning(
                "GitHub MCP enabled for %s but GITHUB_PROJECT_CONNECTION_ID is empty — skipping",
                module_name,
            )
        else:
            from azure.ai.projects.models import MCPTool

            tools.append(
                MCPTool(
                    server_label="github",
                    server_url="https://api.githubcopilot.com/mcp",
                    require_approval="never",
                    project_connection_id=connection_id,
                )
            )
            logger.info("Added GitHub MCP tool for %s", module_name)

    return tools
