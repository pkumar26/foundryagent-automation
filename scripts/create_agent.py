"""Scaffold a new Azure AI Foundry agent.

Generates agent directory, test stubs, and registry entry from a name
or YAML input file. Uses only Python standard library — no external
dependencies.
"""

from __future__ import annotations

import argparse
import keyword
import re
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "agents" / "registry.py"
AGENTS_DIR = REPO_ROOT / "agents"
TESTS_DIR = REPO_ROOT / "tests"

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 50

PREFIX = "[scaffold]"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def validate_name(name: str) -> str | None:
    """Validate an agent name.

    Returns None on success, or an error message string on failure.
    """
    if not name:
        return "Agent name is required."
    if len(name) > MAX_NAME_LENGTH:
        return "Agent name exceeds maximum length of 50 characters."
    if not NAME_PATTERN.match(name):
        return f"Invalid agent name '{name}'. " "Must be lowercase kebab-case (e.g., my-agent)."
    # Check the snake_case form against Python reserved words
    module = name.replace("-", "_")
    if keyword.iskeyword(module):
        return f"Agent name '{name}' is a Python reserved word."
    return None


# ---------------------------------------------------------------------------
# Name derivation helpers
# ---------------------------------------------------------------------------
def to_module_name(name: str) -> str:
    """Convert kebab-case name to snake_case module name."""
    return name.replace("-", "_")


def to_class_prefix(name: str) -> str:
    """Convert kebab-case name to PascalCase class prefix."""
    return "".join(part.capitalize() for part in name.split("-"))


def to_config_class_name(name: str) -> str:
    """Convert kebab-case name to PascalCase config class name."""
    return to_class_prefix(name) + "Config"


def to_display_name(name: str) -> str:
    """Convert kebab-case name to human-readable display name."""
    return name.replace("-", " ").title()


# ---------------------------------------------------------------------------
# Existence checks
# ---------------------------------------------------------------------------
def check_existence(
    name: str,
    module_name: str,
    agents_dir: Path | None = None,
    tests_dir: Path | None = None,
    registry_path: Path | None = None,
) -> str | None:
    """Check that the agent does not already exist.

    Returns None on success, or an error message string on failure.
    """
    _agents_dir = agents_dir or AGENTS_DIR
    _tests_dir = tests_dir or TESTS_DIR
    _registry_path = registry_path or REGISTRY_PATH

    agent_dir = _agents_dir / module_name
    if agent_dir.exists():
        try:
            rel = agent_dir.relative_to(REPO_ROOT)
        except ValueError:
            rel = agent_dir
        return f"Agent '{name}' already exists at {rel}"

    test_dir = _tests_dir / module_name
    if test_dir.exists():
        try:
            rel = test_dir.relative_to(REPO_ROOT)
        except ValueError:
            rel = test_dir
        return f"Test directory already exists at {rel}"

    if _registry_path.exists():
        content = _registry_path.read_text(encoding="utf-8")
        if f'name="{name}"' in content:
            try:
                rel = _registry_path.relative_to(REPO_ROOT)
            except ValueError:
                rel = _registry_path
            return f"Agent '{name}' is already registered in {rel}"

    return None


# ---------------------------------------------------------------------------
# File writing utility
# ---------------------------------------------------------------------------
def _write_file(path: Path, content: str) -> None:
    """Write *content* to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Agent file templates
# ---------------------------------------------------------------------------
def _template_config(
    class_prefix: str,
    agent_name: str,
    model: str,
    module_name: str,
) -> str:
    """Return config.py content for the scaffolded agent."""
    config_cls = f"{class_prefix}Config"
    instructions_path = f"agents/{module_name}/instructions.md"
    return textwrap.dedent(f'''\
        """Configuration for the {agent_name} agent."""

        from agents._base.config import FoundryBaseConfig


        class {config_cls}(FoundryBaseConfig):
            """{class_prefix} agent configuration.

            Extends the base config with agent-specific settings and defaults.
            """

            agent_name: str = "{agent_name}"
            agent_model: str = "{model}"
            agent_instructions_path: str = "{instructions_path}"
            knowledge_source_enabled: bool = False
            github_openapi_enabled: bool = False
            azure_ai_search_connection_id: str = ""
            azure_ai_search_index_name: str = ""
            github_openapi_connection_id: str = ""
    ''')


def _template_instructions(display_name: str) -> str:
    """Return instructions.md content for the scaffolded agent."""
    return textwrap.dedent(f"""\
        # {display_name} Agent

        You are a helpful assistant called **{display_name}**.
        Your role is to assist users with their tasks.

        ## Capabilities

        - Answer questions clearly and concisely
        - Use available tools when they can help answer a question
        - Provide examples when appropriate

        ## Guidelines

        - Be concise and direct in your responses
        - If you're unsure about something, say so rather than guessing
        - Prioritise correctness and security in all suggestions
        - Follow established conventions and patterns
    """)


def _template_sample_tool(display_name: str) -> str:
    """Return sample_tool.py content for the scaffolded agent."""
    return textwrap.dedent(f'''\
        """Sample tool for the {display_name.lower()} agent — a greeting function."""

        from agents._base.tools import create_function_tool


        def greet_user(name: str) -> str:
            """Greet a user by name.

            Args:
                name: The name of the user to greet.

            Returns:
                A personalised greeting message.
            """
            return f"Hello, {{name}}! I\'m the {display_name} agent. How can I assist you today?"


        # Exported tools list — consumed by agent_factory via TOOLS
        TOOLS = [create_function_tool([greet_user])]
    ''')


def _template_tools_init(module_name: str) -> str:
    """Return tools/__init__.py content for the scaffolded agent."""
    return textwrap.dedent(f'''\
        """{module_name.replace("_", "-")} agent tools."""

        from agents.{module_name}.tools.sample_tool import TOOLS

        __all__ = ["TOOLS"]
    ''')


def _template_github_openapi(module_name: str) -> str:
    """Return integrations/github_openapi.py content for the scaffolded agent."""
    agent_label = module_name.replace("_", "-")
    return textwrap.dedent(f'''
        """GitHub OpenAPI integration for the {agent_label} agent.

        Re-exports the shared GitHub OpenAPI tool from the base integrations module.
        To customise, replace the import with your own implementation.
        See docs/openapi-integration-guide.md for setup instructions.
        """

        from agents._base.integrations.github_openapi import get_github_openapi_tool  # noqa: F401

        __all__ = ["get_github_openapi_tool"]
    ''')


def _template_knowledge(module_name: str) -> str:
    """Return integrations/knowledge.py content for the scaffolded agent."""
    agent_label = module_name.replace("_", "-")
    return textwrap.dedent(f'''\
        """Knowledge source integration stub for the {agent_label} agent."""

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
            raise NotImplementedError(
                "Knowledge source integration is not yet implemented. "
                "Set KNOWLEDGE_SOURCE_ENABLED=false to disable."
            )
    ''')


# ---------------------------------------------------------------------------
# Test file templates
# ---------------------------------------------------------------------------
def _template_conftest(module_name: str, config_class_name: str) -> str:
    """Return conftest.py content for the scaffolded agent's tests."""
    agent_label = module_name.replace("_", "-")
    marker = module_name
    return textwrap.dedent(f'''\
        """Conftest for {agent_label} agent tests."""

        import pytest

        from agents.{module_name}.config import {config_class_name}

        pytestmark = pytest.mark.{marker}


        @pytest.fixture
        def {module_name}_config(tmp_path):
            """Create a {config_class_name} with a temp instructions file."""
            instructions_file = tmp_path / "instructions.md"
            instructions_file.write_text("You are a {agent_label} agent.")

            with pytest.MonkeyPatch.context() as m:
                m.setenv("FOUNDRY_PROJECT_CONNECTION_STRING", "test-conn-str")
                config = {config_class_name}(
                    agent_instructions_path=str(instructions_file),
                )
            return config
    ''')


def _template_test_tools(module_name: str, display_name: str) -> str:
    """Return test_tools.py content for the scaffolded agent's tests."""
    marker = module_name
    return textwrap.dedent(f'''\
        """Unit tests for {module_name.replace("_", "-")} agent tools."""

        import pytest

        from agents.{module_name}.tools.sample_tool import greet_user

        pytestmark = pytest.mark.{marker}


        class TestGreetUser:
            """Tests for the greet_user tool function."""

            def test_greets_with_name(self):
                """Should return a greeting with the given name."""
                result = greet_user("Alice")
                assert "Alice" in result
                assert "Hello" in result

            def test_greets_with_empty_name(self):
                """Should handle empty string name."""
                result = greet_user("")
                assert "Hello" in result

            def test_returns_string(self):
                """Should always return a string."""
                result = greet_user("Bob")
                assert isinstance(result, str)

            def test_contains_agent_identifier(self):
                """Should identify itself as {display_name}."""
                result = greet_user("Test")
                assert "{display_name}" in result
    ''')


def _template_test_agent_create(module_name: str, agent_name: str) -> str:
    """Return test_agent_create.py content for the scaffolded agent's tests."""
    marker = module_name
    return textwrap.dedent(f'''\
        """Integration tests for {agent_name} agent creation and update."""

        import os
        import time

        import pytest

        pytestmark = [pytest.mark.integration, pytest.mark.{marker}]

        # Skip all tests in this module if no connection string
        CONNECTION_STRING = os.environ.get("FOUNDRY_PROJECT_CONNECTION_STRING")
        if not CONNECTION_STRING:
            pytest.skip(
                "FOUNDRY_PROJECT_CONNECTION_STRING not set — skipping integration tests",
                allow_module_level=True,
            )


        @pytest.fixture
        def test_agent_name():
            """Generate a unique test agent name with prefix and timestamp."""
            return f"test-{agent_name}-{{int(time.time())}}"


        @pytest.fixture
        def agents_client():
            """Create a real AgentsClient for integration testing."""
            from azure.ai.agents import AgentsClient
            from azure.identity import DefaultAzureCredential

            client = AgentsClient(
                endpoint=CONNECTION_STRING,
                credential=DefaultAzureCredential(),
            )
            return client


        @pytest.fixture
        def cleanup_agent(agents_client, test_agent_name):
            """Fixture that yields and then cleans up the test agent."""
            yield
            # Teardown: find and delete test agent
            try:
                for agent in agents_client.list_agents():
                    if agent.name == test_agent_name:
                        agents_client.delete_agent(agent.id)
                        break
            except Exception:
                pass


        class TestAgentCreateIntegration:
            """Integration tests for agent creation against live Foundry."""

            def test_create_agent(self, agents_client, test_agent_name, cleanup_agent):
                """Should create a new agent in Foundry."""
                agent = agents_client.create_agent(
                    model="gpt-4o",
                    name=test_agent_name,
                    instructions="You are a test agent.",
                )
                assert agent.name == test_agent_name
    ''')


def _template_test_agent_run(module_name: str, agent_name: str) -> str:
    """Return test_agent_run.py content for the scaffolded agent's tests."""
    marker = module_name
    return textwrap.dedent(f'''\
        """Integration tests for {agent_name} agent run lifecycle."""

        import os
        import time

        import pytest

        pytestmark = [pytest.mark.integration, pytest.mark.{marker}]

        # Skip all tests in this module if no connection string
        CONNECTION_STRING = os.environ.get("FOUNDRY_PROJECT_CONNECTION_STRING")
        if not CONNECTION_STRING:
            pytest.skip(
                "FOUNDRY_PROJECT_CONNECTION_STRING not set — skipping integration tests",
                allow_module_level=True,
            )


        @pytest.fixture
        def test_agent_name():
            """Generate a unique test agent name."""
            return f"test-{agent_name}-run-{{int(time.time())}}"


        @pytest.fixture
        def agents_client():
            """Create a real agents client."""
            from azure.ai.agents import AgentsClient
            from azure.identity import DefaultAzureCredential

            client = AgentsClient(
                endpoint=CONNECTION_STRING,
                credential=DefaultAzureCredential(),
            )
            return client


        @pytest.fixture
        def test_agent(agents_client, test_agent_name):
            """Create a test agent and clean up after."""
            agent = agents_client.create_agent(
                model="gpt-4o",
                name=test_agent_name,
                instructions="You are a test agent. Always respond with \'Test OK\'.",
            )
            yield agent
            # Teardown
            try:
                agents_client.delete_agent(agent.id)
            except Exception:
                pass


        class TestAgentRunIntegration:
            """Integration tests for the full agent run lifecycle."""

            def test_full_run_lifecycle(self, agents_client, test_agent):
                """Should create thread, post message, run agent, and get response."""
                from azure.ai.agents.models import MessageRole, RunStatus

                # Create thread
                thread = agents_client.threads.create()
                assert thread.id is not None

                try:
                    # Post message
                    agents_client.messages.create(
                        thread_id=thread.id,
                        role="user",
                        content="Hello!",
                    )

                    # Run agent
                    run = agents_client.runs.create_and_process(
                        thread_id=thread.id,
                        agent_id=test_agent.id,
                    )

                    assert run.status == RunStatus.COMPLETED

                    # Get response
                    last_msg = agents_client.messages.get_last_message_text_by_role(
                        thread_id=thread.id,
                        role=MessageRole.AGENT,
                    )

                    assert last_msg is not None
                    assert len(last_msg.text.value) > 0
                finally:
                    try:
                        agents_client.threads.delete(thread.id)
                    except Exception:
                        pass
    ''')


# ---------------------------------------------------------------------------
# File generation
# ---------------------------------------------------------------------------
def _generate_agent_files(
    name: str,
    module_name: str,
    class_prefix: str,
    model: str,
    display_name: str,
    agents_dir: Path | None = None,
) -> list[Path]:
    """Generate all agent files under agents/{module_name}/."""
    base = (agents_dir or AGENTS_DIR) / module_name

    files: list[tuple[Path, str]] = [
        (base / "__init__.py", ""),
        (base / "config.py", _template_config(class_prefix, name, model, module_name)),
        (base / "instructions.md", _template_instructions(display_name)),
        (base / "tools" / "__init__.py", _template_tools_init(module_name)),
        (base / "tools" / "sample_tool.py", _template_sample_tool(display_name)),
        (base / "integrations" / "__init__.py", ""),
        (base / "integrations" / "github_openapi.py", _template_github_openapi(module_name)),
        (base / "integrations" / "knowledge.py", _template_knowledge(module_name)),
    ]

    created: list[Path] = []
    for path, content in files:
        _write_file(path, content)
        created.append(path)
    return created


def _generate_test_files(
    name: str,
    module_name: str,
    class_prefix: str,
    display_name: str,
    tests_dir: Path | None = None,
) -> list[Path]:
    """Generate all test files under tests/{module_name}/."""
    base = (tests_dir or TESTS_DIR) / module_name
    config_cls = to_config_class_name(name)

    files: list[tuple[Path, str]] = [
        (base / "__init__.py", ""),
        (base / "conftest.py", _template_conftest(module_name, config_cls)),
        (base / "test_tools.py", _template_test_tools(module_name, display_name)),
        (
            base / "test_agent_create.py",
            _template_test_agent_create(module_name, name),
        ),
        (base / "test_agent_run.py", _template_test_agent_run(module_name, name)),
    ]

    created: list[Path] = []
    for path, content in files:
        _write_file(path, content)
        created.append(path)
    return created


# ---------------------------------------------------------------------------
# Registry update
# ---------------------------------------------------------------------------
def _update_registry(
    name: str,
    module_name: str,
    config_class_name: str,
    registry_path: Path | None = None,
) -> None:
    """Append a new agent entry to agents/registry.py."""
    path = registry_path or REGISTRY_PATH
    content = path.read_text(encoding="utf-8")

    # Insert import after the last `from agents.*.config import *Config` line
    import_line = f"from agents.{module_name}.config import " f"{config_class_name}  # noqa: E402\n"
    # Find the last existing config import
    last_import_pos = -1
    for match in re.finditer(r"^from agents\.\w+\.config import \w+.*$", content, re.MULTILINE):
        last_import_pos = match.end()

    if last_import_pos == -1:
        _error(f"Could not find config imports in {path}")
        return

    content = content[:last_import_pos] + "\n" + import_line + content[last_import_pos:]

    # Insert new AgentRegistryEntry before the closing    ]\n)
    entry = textwrap.dedent(f"""\
        AgentRegistryEntry(
            name="{name}",
            config_class={config_class_name},
            factory=create_or_update_agent,
        ),
""")

    # Match the real registry format:  4-space-indented "]" followed by ")"
    closing = "    ]\n)\n"
    closing_pos = content.rfind(closing)
    if closing_pos == -1:
        # Fallback: try without trailing newline
        closing = "    ]\n)"
        closing_pos = content.rfind(closing)
    if closing_pos == -1:
        _error(f"Could not find REGISTRY closing in {path}")
        return

    content = content[:closing_pos] + "        " + entry + content[closing_pos:]

    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# YAML input parser
# ---------------------------------------------------------------------------
def _parse_yaml_file(filepath: str) -> dict[str, str]:
    """Parse a simple key: value YAML file (flat subset, no PyYAML).

    Returns a dict of string key-value pairs.
    Raises SystemExit on errors.
    """
    path = Path(filepath)
    if not path.exists():
        _error(f"Input file not found: {filepath}")
        sys.exit(1)

    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        result[key.strip()] = value.strip()

    if "name" not in result:
        _error("Input file missing required field: 'name'")
        sys.exit(1)

    return result


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def _info(msg: str) -> None:
    """Print an informational message."""
    print(f"{PREFIX} {msg}")


def _error(msg: str) -> None:
    """Print an error message to stderr."""
    print(f"{PREFIX} \u2717 {msg}", file=sys.stderr)


def _success(msg: str) -> None:
    """Print a success message."""
    print(f"{PREFIX} \u2713 {msg}")


# ---------------------------------------------------------------------------
# CLI and orchestration
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Scaffold a new Azure AI Foundry agent.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--name",
        help="Agent name in kebab-case (e.g., my-agent)",
    )
    group.add_argument(
        "--from-file",
        help="Path to YAML config file for non-interactive creation",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model name (default: gpt-4o)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the scaffolding script.

    Returns 0 on success, 1 on validation error, 2 on filesystem error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Resolve name and model from either --name or --from-file
    if args.from_file:
        parsed = _parse_yaml_file(args.from_file)
        name = parsed["name"]
        model = parsed.get("model", "gpt-4o")
    else:
        name = args.name
        model = args.model

    # Validate
    err = validate_name(name)
    if err:
        _error(err)
        return 1

    # Derive names
    module_name = to_module_name(name)
    class_prefix = to_class_prefix(name)
    config_cls = to_config_class_name(name)
    display_name = to_display_name(name)

    # Check existence
    err = check_existence(name, module_name)
    if err:
        _error(err)
        return 1

    # Generate files
    try:
        agent_files = _generate_agent_files(name, module_name, class_prefix, model, display_name)
        test_files = _generate_test_files(name, module_name, class_prefix, display_name)
        _update_registry(name, module_name, config_cls)
    except OSError as exc:
        _error(str(exc))
        return 2

    total = len(agent_files) + len(test_files)

    # Print summary
    _success(f"Agent '{name}' scaffolded successfully")
    _info(f"  Created: agents/{module_name}/")
    _info(f"  Created: tests/{module_name}/")
    _info("  Updated: agents/registry.py")
    _info(f"  Files generated: {total}")
    _info("")
    _info("  Next steps:")
    _info(f"  1. Edit agents/{module_name}/instructions.md with agent instructions")
    _info(f"  2. Add custom tools in agents/{module_name}/tools/")
    _info(f"  3. Run tests: pytest tests/{module_name}/ -v")
    _info(f"  4. Deploy: python scripts/deploy_agent.py --agent {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
