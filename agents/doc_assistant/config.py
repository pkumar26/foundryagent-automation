"""Configuration for the doc-assistant agent."""

from agents._base.config import FoundryBaseConfig


class DocAssistantConfig(FoundryBaseConfig):
    """Doc-assistant agent configuration.

    Extends the base config with agent-specific settings and defaults.
    """

    agent_name: str = "doc-assistant"
    agent_model: str = "gpt-4o"
    agent_instructions_path: str = "agents/doc_assistant/instructions.md"
    knowledge_source_enabled: bool = False
    github_mcp_enabled: bool = False
    azure_ai_search_connection_id: str = ""
    azure_ai_search_index_name: str = ""
    github_mcp_connection_id: str = ""
