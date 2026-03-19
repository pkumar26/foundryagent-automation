"""Conftest for code-helper agent tests."""

import pytest

from agents.code_helper.config import CodeHelperConfig

pytestmark = pytest.mark.code_helper


@pytest.fixture
def code_helper_config(tmp_path):
    """Create a CodeHelperConfig with a temp instructions file."""
    instructions_file = tmp_path / "instructions.md"
    instructions_file.write_text("You are a code helper agent.")

    with pytest.MonkeyPatch.context() as m:
        m.setenv("FOUNDRY_PROJECT_CONNECTION_STRING", "test-conn-str")
        config = CodeHelperConfig(
            agent_instructions_path=str(instructions_file),
        )
    return config
