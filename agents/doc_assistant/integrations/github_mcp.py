"""GitHub MCP integration stub for the doc-assistant agent."""

from agents._base.config import FoundryBaseConfig


def get_github_mcp_tool(config: FoundryBaseConfig):
    """Return a GitHub MCP tool definition, or None if disabled.

    Args:
        config: Agent configuration with github_mcp_enabled flag.

    Returns:
        Tool definition when enabled (future implementation), None when disabled.
    """
    if not getattr(config, "github_mcp_enabled", False):
        return None
    # Future: return GitHub MCP tool definition
    return None
