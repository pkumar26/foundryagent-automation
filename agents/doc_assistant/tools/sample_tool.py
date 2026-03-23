"""Sample tool for the doc-assistant agent — a text summarisation function."""

from agents._base.tools import create_function_tool


def summarise_text(text: str, max_sentences: int = 3) -> str:
    """Summarise a block of text into a shorter form.

    Args:
        text: The text to summarise.
        max_sentences: Maximum number of sentences in the summary.

    Returns:
        A shortened version of the input text.
    """
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    summary = ". ".join(sentences[:max_sentences])
    if summary and not summary.endswith("."):
        summary += "."
    return summary


# Exported tools list — consumed by agent_factory via TOOLS
TOOLS = [create_function_tool(summarise_text)]
