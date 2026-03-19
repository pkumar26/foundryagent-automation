"""Knowledge source integration stub for the doc-assistant agent."""

from agents._base.config import FoundryBaseConfig


def get_knowledge_tool(config: FoundryBaseConfig):
    """Return a knowledge source tool definition, or None if disabled.

    Args:
        config: Agent configuration with knowledge_source_enabled flag.

    Returns:
        Tool definition when enabled (future implementation), None when disabled.
    """
    if not getattr(config, "knowledge_source_enabled", False):
        return None
    # Future: return Azure AI Search tool definition
    return None
