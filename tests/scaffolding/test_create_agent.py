"""Tests for the agent scaffolding script (scripts/create_agent.py)."""

import sys
import textwrap
import time
from pathlib import Path

import pytest

# Add scripts/ to path so we can import create_agent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from create_agent import (  # noqa: E402
    _generate_agent_files,
    _generate_test_files,
    _parse_yaml_file,
    _update_registry,
    build_parser,
    check_existence,
    to_class_prefix,
    to_config_class_name,
    to_display_name,
    to_module_name,
    validate_name,
)

pytestmark = pytest.mark.scaffolding


# ---- Mock registry content for tests ----
MOCK_REGISTRY = textwrap.dedent('''\
    """Agent registry — central mapping of agent names to their config and factory."""

    from dataclasses import dataclass
    from typing import Callable, Type

    from agents._base.config import FoundryBaseConfig


    @dataclass(frozen=True)
    class AgentRegistryEntry:
        name: str
        config_class: Type[FoundryBaseConfig]
        factory: Callable


    class AgentRegistry:
        def __init__(self, entries):
            self._entries = list(entries)


    from agents._base.agent_factory import create_or_update_agent  # noqa: E402
    from agents.code_helper.config import CodeHelperConfig  # noqa: E402

    REGISTRY = AgentRegistry(
        [
            AgentRegistryEntry(
                name="code-helper",
                config_class=CodeHelperConfig,
                factory=create_or_update_agent,
            ),
        ]
    )
''')


# ===========================================================================
# T008: test_validate_name_valid / test_validate_name_invalid
# ===========================================================================
class TestValidateName:
    """Tests for the validate_name function."""

    @pytest.mark.parametrize(
        "name",
        [
            "my-agent",
            "agent1",
            "a",
            "code-helper-v2",
            "x-y-z",
            "agent123",
        ],
    )
    def test_validate_name_valid(self, name: str) -> None:
        """Valid kebab-case names should pass validation."""
        assert validate_name(name) is None

    @pytest.mark.parametrize(
        "name,expected_fragment",
        [
            ("", "required"),
            ("My-Agent", "kebab-case"),
            ("my_agent", "kebab-case"),
            ("my agent", "kebab-case"),
            ("-leading", "kebab-case"),
            ("trailing-", "kebab-case"),
            ("MY-AGENT", "kebab-case"),
            ("a" * 51, "maximum length"),
        ],
    )
    def test_validate_name_invalid(self, name: str, expected_fragment: str) -> None:
        """Invalid names should return an error message containing expected text."""
        result = validate_name(name)
        assert result is not None
        assert expected_fragment.lower() in result.lower()

    def test_validate_name_reserved_word(self) -> None:
        """Python reserved words (in snake_case form) should be rejected."""
        # 'for' is a keyword; 'f-or' maps to module 'f_or' which isn't,
        # but let's test one that IS: 'class' -> module 'class'
        result = validate_name("class")
        assert result is not None
        assert "reserved word" in result.lower()


# ===========================================================================
# T009: test_name_derivation
# ===========================================================================
class TestNameDerivation:
    """Tests for name derivation helpers."""

    def test_to_module_name(self) -> None:
        assert to_module_name("my-agent") == "my_agent"
        assert to_module_name("code-helper-v2") == "code_helper_v2"
        assert to_module_name("simple") == "simple"

    def test_to_class_prefix(self) -> None:
        assert to_class_prefix("my-agent") == "MyAgent"
        assert to_class_prefix("code-helper-v2") == "CodeHelperV2"
        assert to_class_prefix("simple") == "Simple"

    def test_to_config_class_name(self) -> None:
        assert to_config_class_name("my-agent") == "MyAgentConfig"
        assert to_config_class_name("code-helper") == "CodeHelperConfig"

    def test_to_display_name(self) -> None:
        assert to_display_name("my-agent") == "My Agent"
        assert to_display_name("code-helper") == "Code Helper"


# ===========================================================================
# T010: test_scaffold_creates_agent_directory
# ===========================================================================
class TestScaffoldCreatesAgentDirectory:
    """Tests for agent directory and file generation."""

    def test_scaffold_creates_agent_directory(self, tmp_path: Path) -> None:
        """Should create all 8 agent files with correct content."""
        start = time.monotonic()

        files = _generate_agent_files(
            name="test-agent",
            module_name="test_agent",
            class_prefix="TestAgent",
            model="gpt-4o",
            display_name="Test Agent",
            agents_dir=tmp_path,
        )
        elapsed = time.monotonic() - start

        # NFR-4: < 2s
        assert elapsed < 2.0

        assert len(files) == 8

        agent_dir = tmp_path / "test_agent"
        assert (agent_dir / "__init__.py").exists()
        assert (agent_dir / "config.py").exists()
        assert (agent_dir / "instructions.md").exists()
        assert (agent_dir / "tools" / "__init__.py").exists()
        assert (agent_dir / "tools" / "sample_tool.py").exists()
        assert (agent_dir / "integrations" / "__init__.py").exists()
        assert (agent_dir / "integrations" / "github_openapi.py").exists()
        assert (agent_dir / "integrations" / "knowledge.py").exists()

        # Verify config content
        config_content = (agent_dir / "config.py").read_text()
        assert "class TestAgentConfig(FoundryBaseConfig):" in config_content
        assert 'agent_name: str = "test-agent"' in config_content
        assert 'agent_model: str = "gpt-4o"' in config_content

        # Verify instructions content
        instructions = (agent_dir / "instructions.md").read_text()
        assert "Test Agent" in instructions

        # Verify sample tool
        tool_content = (agent_dir / "tools" / "sample_tool.py").read_text()
        assert "Test Agent" in tool_content
        assert "TOOLS" in tool_content

        # Verify tools __init__
        tools_init = (agent_dir / "tools" / "__init__.py").read_text()
        assert "from agents.test_agent.tools.sample_tool import TOOLS" in tools_init


# ===========================================================================
# T011: test_scaffold_creates_test_directory
# ===========================================================================
class TestScaffoldCreatesTestDirectory:
    """Tests for test directory and file generation."""

    def test_scaffold_creates_test_directory(self, tmp_path: Path) -> None:
        """Should create all 5 test files with correct content."""
        files = _generate_test_files(
            name="test-agent",
            module_name="test_agent",
            class_prefix="TestAgent",
            display_name="Test Agent",
            tests_dir=tmp_path,
        )

        assert len(files) == 5

        test_dir = tmp_path / "test_agent"
        assert (test_dir / "__init__.py").exists()
        assert (test_dir / "conftest.py").exists()
        assert (test_dir / "test_tools.py").exists()
        assert (test_dir / "test_agent_create.py").exists()
        assert (test_dir / "test_agent_run.py").exists()

        # Verify conftest content
        conftest = (test_dir / "conftest.py").read_text()
        assert "TestAgentConfig" in conftest
        assert "from agents.test_agent.config import TestAgentConfig" in conftest

        # Verify test_tools content
        test_tools = (test_dir / "test_tools.py").read_text()
        assert "from agents.test_agent.tools.sample_tool import greet_user" in test_tools
        assert "Test Agent" in test_tools


# ===========================================================================
# T012: test_scaffold_updates_registry
# ===========================================================================
class TestScaffoldUpdatesRegistry:
    """Tests for registry.py modification."""

    def test_scaffold_updates_registry(self, tmp_path: Path) -> None:
        """Should append import and AgentRegistryEntry to registry file."""
        registry_file = tmp_path / "registry.py"
        registry_file.write_text(MOCK_REGISTRY)

        _update_registry(
            name="new-agent",
            module_name="new_agent",
            config_class_name="NewAgentConfig",
            registry_path=registry_file,
        )

        content = registry_file.read_text()

        # Verify import was added
        assert "from agents.new_agent.config import NewAgentConfig" in content

        # Verify entry was added
        assert 'name="new-agent"' in content
        assert "config_class=NewAgentConfig" in content

        # Verify existing content is preserved
        assert 'name="code-helper"' in content
        assert "CodeHelperConfig" in content


# ===========================================================================
# T013: test_scaffold_rejects_existing_agent
# ===========================================================================
class TestScaffoldRejectsExistingAgent:
    """Tests for idempotency guard."""

    def test_rejects_existing_agent_dir(self, tmp_path: Path) -> None:
        """Should return error when agent directory already exists."""
        agents_dir = tmp_path / "agents"
        (agents_dir / "my_agent").mkdir(parents=True)

        result = check_existence(
            name="my-agent",
            module_name="my_agent",
            agents_dir=agents_dir,
            tests_dir=tmp_path / "tests",
            registry_path=tmp_path / "empty_registry.py",
        )

        assert result is not None
        assert "already exists" in result

    def test_rejects_existing_test_dir(self, tmp_path: Path) -> None:
        """Should return error when test directory already exists."""
        tests_dir = tmp_path / "tests"
        (tests_dir / "my_agent").mkdir(parents=True)

        result = check_existence(
            name="my-agent",
            module_name="my_agent",
            agents_dir=tmp_path / "agents",
            tests_dir=tests_dir,
            registry_path=tmp_path / "empty_registry.py",
        )

        assert result is not None
        assert "already exists" in result

    def test_rejects_existing_registry_entry(self, tmp_path: Path) -> None:
        """Should return error when agent is already in registry."""
        registry_file = tmp_path / "registry.py"
        registry_file.write_text(MOCK_REGISTRY)

        result = check_existence(
            name="code-helper",
            module_name="code_helper",
            agents_dir=tmp_path / "agents",
            tests_dir=tmp_path / "tests",
            registry_path=registry_file,
        )

        assert result is not None
        assert "already registered" in result


# ===========================================================================
# T022: test_parse_yaml_valid
# ===========================================================================
class TestParseYamlValid:
    """Tests for YAML file parsing."""

    def test_parse_yaml_valid(self, tmp_path: Path) -> None:
        """Valid YAML with name+model should parse correctly."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("name: my-agent\nmodel: gpt-4o-mini\n")

        result = _parse_yaml_file(str(yaml_file))

        assert result["name"] == "my-agent"
        assert result["model"] == "gpt-4o-mini"

    def test_parse_yaml_name_only(self, tmp_path: Path) -> None:
        """YAML with only name should parse (model optional)."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("name: simple-agent\n")

        result = _parse_yaml_file(str(yaml_file))

        assert result["name"] == "simple-agent"
        assert "model" not in result

    def test_parse_yaml_with_comments(self, tmp_path: Path) -> None:
        """YAML with comments and blank lines should parse correctly."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("# This is a config\nname: my-agent\n\n# Optional\nmodel: gpt-4o\n")

        result = _parse_yaml_file(str(yaml_file))

        assert result["name"] == "my-agent"
        assert result["model"] == "gpt-4o"


# ===========================================================================
# T023: test_parse_yaml_missing_name
# ===========================================================================
class TestParseYamlMissingName:
    """Tests for YAML parsing error handling."""

    def test_parse_yaml_missing_name(self, tmp_path: Path) -> None:
        """Missing name field should raise SystemExit."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("model: gpt-4o\n")

        with pytest.raises(SystemExit):
            _parse_yaml_file(str(yaml_file))


# ===========================================================================
# T024: test_parse_yaml_file_not_found
# ===========================================================================
class TestParseYamlFileNotFound:
    """Tests for missing YAML file."""

    def test_parse_yaml_file_not_found(self, tmp_path: Path) -> None:
        """Non-existent file path should raise SystemExit."""
        with pytest.raises(SystemExit):
            _parse_yaml_file(str(tmp_path / "nonexistent.yaml"))


# ===========================================================================
# T025: test_scaffold_from_yaml
# ===========================================================================
class TestScaffoldFromYaml:
    """End-to-end tests for YAML-based scaffolding."""

    def test_scaffold_from_yaml(self, tmp_path: Path) -> None:
        """YAML file should generate same files as CLI mode."""
        # Setup directories
        agents_dir = tmp_path / "agents"
        tests_dir = tmp_path / "tests"
        registry_file = tmp_path / "registry.py"
        registry_file.write_text(MOCK_REGISTRY)

        # Create YAML file
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("name: yaml-agent\nmodel: gpt-4o\n")

        # Parse and scaffold
        parsed = _parse_yaml_file(str(yaml_file))

        agent_files = _generate_agent_files(
            name=parsed["name"],
            module_name=to_module_name(parsed["name"]),
            class_prefix=to_class_prefix(parsed["name"]),
            model=parsed.get("model", "gpt-4o"),
            display_name=to_display_name(parsed["name"]),
            agents_dir=agents_dir,
        )

        test_files = _generate_test_files(
            name=parsed["name"],
            module_name=to_module_name(parsed["name"]),
            class_prefix=to_class_prefix(parsed["name"]),
            display_name=to_display_name(parsed["name"]),
            tests_dir=tests_dir,
        )

        # Same file count as CLI
        assert len(agent_files) == 8
        assert len(test_files) == 5

        # Verify agent dir was created
        assert (agents_dir / "yaml_agent" / "config.py").exists()
        assert (tests_dir / "yaml_agent" / "conftest.py").exists()


# ===========================================================================
# T025b: test_from_file_ignores_cli_model
# ===========================================================================
class TestFromFileIgnoresCliModel:
    """Tests for --from-file / --model precedence."""

    def test_from_file_ignores_cli_model(self, tmp_path: Path) -> None:
        """When --from-file is used, model from YAML takes precedence."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("name: precedence-test\nmodel: gpt-4o-mini\n")

        parsed = _parse_yaml_file(str(yaml_file))

        # The main() function uses parsed model, ignoring args.model
        # Verify the parser returns the YAML model
        assert parsed["model"] == "gpt-4o-mini"

        # Verify that build_parser allows both flags syntactically
        parser = build_parser()
        args = parser.parse_args(["--from-file", str(yaml_file), "--model", "gpt-4o"])
        # When --from-file is used, main() reads model from file not args
        assert args.from_file == str(yaml_file)
