"""Configuration for the code-helper agent."""

from agents._base.config import FoundryBaseConfig


class CodeHelperConfig(FoundryBaseConfig):
    """Code-helper agent configuration.

    Extends the base config with agent-specific settings and defaults.
    """

    agent_name: str = "code-helper"
    agent_model: str = "gpt-4o"
    agent_instructions_path: str = "agents/code_helper/instructions.md"
    knowledge_source_enabled: bool = False
    github_openapi_enabled: bool = False
    azure_ai_search_connection_id: str = ""
    azure_ai_search_index_name: str = ""
    github_openapi_connection_id: str = ""
