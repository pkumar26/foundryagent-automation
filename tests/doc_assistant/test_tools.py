"""Unit tests for doc-assistant agent tools."""

import pytest

from agents.doc_assistant.tools.sample_tool import summarise_text

pytestmark = pytest.mark.doc_assistant


class TestSummariseText:
    """Tests for the summarise_text tool function."""

    def test_summarises_to_max_sentences(self):
        """Should truncate text to max_sentences."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        result = summarise_text(text, max_sentences=2)
        assert "First sentence" in result
        assert "Second sentence" in result
        assert "Third sentence" not in result

    def test_handles_short_text(self):
        """Should return text as-is when fewer than max sentences."""
        text = "Only one sentence."
        result = summarise_text(text, max_sentences=3)
        assert "Only one sentence" in result

    def test_handles_empty_text(self):
        """Should handle empty string input."""
        result = summarise_text("")
        assert result == ""

    def test_returns_string(self):
        """Should always return a string."""
        result = summarise_text("Some text here. And more text.")
        assert isinstance(result, str)

    def test_default_max_sentences(self):
        """Should default to 3 sentences when max_sentences is not specified."""
        text = "One. Two. Three. Four. Five."
        result = summarise_text(text)
        # Should have at most 3 sentences
        sentences = [s.strip() for s in result.split(".") if s.strip()]
        assert len(sentences) <= 3
