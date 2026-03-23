"""Unit tests for the agent deletion script."""

import textwrap

from scripts.delete_agent import (
    _get_all_agent_names,
    check_agent_exists,
    main,
    remove_directory,
    remove_registry_entry,
    to_config_class_name,
    to_module_name,
)


# ---------------------------------------------------------------------------
# Name helpers
# ---------------------------------------------------------------------------
class TestNameHelpers:
    """Tests for name conversion helpers."""

    def test_to_module_name(self):
        assert to_module_name("my-agent") == "my_agent"

    def test_to_config_class_name(self):
        assert to_config_class_name("my-agent") == "MyAgentConfig"

    def test_to_config_class_name_single_word(self):
        assert to_config_class_name("agent") == "AgentConfig"


# ---------------------------------------------------------------------------
# Existence checks
# ---------------------------------------------------------------------------
class TestCheckAgentExists:
    """Tests for check_agent_exists."""

    def test_nothing_exists(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        registry = tmp_path / "registry.py"
        registry.write_text("REGISTRY = AgentRegistry([])")

        result = check_agent_exists(
            "my-agent",
            "my_agent",
            agents_dir=agents_dir,
            tests_dir=tests_dir,
            registry_path=registry,
        )
        assert result == (False, False, False)

    def test_all_exist(self, tmp_path):
        agents_dir = tmp_path / "agents"
        (agents_dir / "my_agent").mkdir(parents=True)
        tests_dir = tmp_path / "tests"
        (tests_dir / "my_agent").mkdir(parents=True)
        registry = tmp_path / "registry.py"
        registry.write_text('name="my-agent"')

        result = check_agent_exists(
            "my-agent",
            "my_agent",
            agents_dir=agents_dir,
            tests_dir=tests_dir,
            registry_path=registry,
        )
        assert result == (True, True, True)

    def test_partial_exists(self, tmp_path):
        agents_dir = tmp_path / "agents"
        (agents_dir / "my_agent").mkdir(parents=True)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        registry = tmp_path / "registry.py"
        registry.write_text("empty")

        result = check_agent_exists(
            "my-agent",
            "my_agent",
            agents_dir=agents_dir,
            tests_dir=tests_dir,
            registry_path=registry,
        )
        assert result == (True, False, False)


# ---------------------------------------------------------------------------
# Registry cleanup
# ---------------------------------------------------------------------------
class TestRemoveRegistryEntry:
    """Tests for remove_registry_entry."""

    def test_removes_import_and_entry(self, tmp_path):
        registry = tmp_path / "registry.py"
        registry.write_text(textwrap.dedent("""\
            from agents._base.agent_factory import create_or_update_agent  # noqa: E402
            from agents.code_helper.config import CodeHelperConfig  # noqa: E402
            from agents.my_agent.config import MyAgentConfig  # noqa: E402

            REGISTRY = AgentRegistry(
                [
                    AgentRegistryEntry(
                        name="code-helper",
                        config_class=CodeHelperConfig,
                        factory=create_or_update_agent,
                    ),
                    AgentRegistryEntry(
                        name="my-agent",
                        config_class=MyAgentConfig,
                        factory=create_or_update_agent,
                    ),
                ]
            )
        """))

        result = remove_registry_entry(
            "my-agent",
            "my_agent",
            "MyAgentConfig",
            registry_path=registry,
        )
        assert result is True

        content = registry.read_text()
        assert "my_agent" not in content
        assert "MyAgentConfig" not in content
        assert "my-agent" not in content
        # Other entries should remain
        assert "code-helper" in content
        assert "CodeHelperConfig" in content

    def test_handles_unindented_entry(self, tmp_path):
        """Registry entries created by scaffolding may have varied indentation."""
        registry = tmp_path / "registry.py"
        registry.write_text(textwrap.dedent("""\
            from agents.my_agent.config import MyAgentConfig  # noqa: E402

            REGISTRY = AgentRegistry(
                [
                    AgentRegistryEntry(
                name="my-agent",
                config_class=MyAgentConfig,
                factory=create_or_update_agent,
            ),
                ]
            )
        """))

        result = remove_registry_entry(
            "my-agent",
            "my_agent",
            "MyAgentConfig",
            registry_path=registry,
        )
        assert result is True
        content = registry.read_text()
        assert "my-agent" not in content

    def test_returns_false_when_not_found(self, tmp_path):
        registry = tmp_path / "registry.py"
        registry.write_text("REGISTRY = AgentRegistry([])")

        result = remove_registry_entry(
            "nonexistent",
            "nonexistent",
            "NonexistentConfig",
            registry_path=registry,
        )
        assert result is False

    def test_returns_false_when_file_missing(self, tmp_path):
        result = remove_registry_entry(
            "my-agent",
            "my_agent",
            "MyAgentConfig",
            registry_path=tmp_path / "nonexistent.py",
        )
        assert result is False


# ---------------------------------------------------------------------------
# Directory removal
# ---------------------------------------------------------------------------
class TestRemoveDirectory:
    """Tests for remove_directory."""

    def test_removes_existing_directory(self, tmp_path):
        target = tmp_path / "my_agent"
        target.mkdir()
        (target / "config.py").write_text("x")

        assert remove_directory(target) is True
        assert not target.exists()

    def test_returns_false_for_nonexistent(self, tmp_path):
        assert remove_directory(tmp_path / "nope") is False


# ---------------------------------------------------------------------------
# CLI (main)
# ---------------------------------------------------------------------------
class TestMainCLI:
    """Tests for the main() entry point."""

    def test_returns_1_when_agent_not_found(self):
        result = main(["--name", "nonexistent-agent-xyz", "--force"])
        assert result == 1

    def test_returns_0_on_successful_delete(self, tmp_path, monkeypatch):
        """End-to-end: scaffold dirs + registry, then delete."""
        # Set up agent dir
        agent_dir = tmp_path / "agents" / "test_del"
        agent_dir.mkdir(parents=True)
        (agent_dir / "config.py").write_text("x")

        # Set up test dir
        test_dir = tmp_path / "tests" / "test_del"
        test_dir.mkdir(parents=True)

        # Set up registry
        registry = tmp_path / "agents" / "registry.py"
        registry.write_text(textwrap.dedent("""\
            from agents.test_del.config import TestDelConfig  # noqa: E402

            REGISTRY = AgentRegistry(
                [
                    AgentRegistryEntry(
                        name="test-del",
                        config_class=TestDelConfig,
                        factory=create_or_update_agent,
                    ),
                ]
            )
        """))

        # Monkeypatch module-level paths
        import scripts.delete_agent as mod

        monkeypatch.setattr(mod, "AGENTS_DIR", tmp_path / "agents")
        monkeypatch.setattr(mod, "TESTS_DIR", tmp_path / "tests")
        monkeypatch.setattr(mod, "REGISTRY_PATH", registry)

        result = main(["--name", "test-del", "--force", "--no-portal"])
        assert result == 0

        assert not agent_dir.exists()
        assert not test_dir.exists()
        content = registry.read_text()
        assert "test-del" not in content

    def test_cancellation_without_force(self, tmp_path, monkeypatch):
        """Should return 1 when user types 'n'."""
        agent_dir = tmp_path / "agents" / "cancel_me"
        agent_dir.mkdir(parents=True)

        import scripts.delete_agent as mod

        monkeypatch.setattr(mod, "AGENTS_DIR", tmp_path / "agents")
        monkeypatch.setattr(mod, "TESTS_DIR", tmp_path / "tests")
        monkeypatch.setattr(mod, "REGISTRY_PATH", tmp_path / "reg.py")
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = main(["--name", "cancel-me"])
        assert result == 1
        # Directory should still exist
        assert agent_dir.exists()


# ---------------------------------------------------------------------------
# _get_all_agent_names
# ---------------------------------------------------------------------------
class TestGetAllAgentNames:
    """Tests for _get_all_agent_names."""

    def test_returns_names_from_registry(self, tmp_path, monkeypatch):
        registry = tmp_path / "registry.py"
        registry.write_text(textwrap.dedent("""\
            AgentRegistryEntry(
                name="code-helper",
                config_class=CodeHelperConfig,
                factory=create_or_update_agent,
            ),
            AgentRegistryEntry(
                name="doc-assistant",
                config_class=DocAssistantConfig,
                factory=create_or_update_agent,
            ),
        """))

        import scripts.delete_agent as mod

        monkeypatch.setattr(mod, "REGISTRY_PATH", registry)
        assert _get_all_agent_names() == ["code-helper", "doc-assistant"]

    def test_returns_empty_when_no_file(self, tmp_path, monkeypatch):
        import scripts.delete_agent as mod

        monkeypatch.setattr(mod, "REGISTRY_PATH", tmp_path / "nope.py")
        assert _get_all_agent_names() == []

    def test_returns_empty_when_no_entries(self, tmp_path, monkeypatch):
        registry = tmp_path / "registry.py"
        registry.write_text("REGISTRY = AgentRegistry([])")

        import scripts.delete_agent as mod

        monkeypatch.setattr(mod, "REGISTRY_PATH", registry)
        assert _get_all_agent_names() == []


# ---------------------------------------------------------------------------
# CLI --all
# ---------------------------------------------------------------------------
class TestDeleteAll:
    """Tests for --all flag."""

    def test_delete_all_succeeds(self, tmp_path, monkeypatch):
        """--all --force deletes all registered agents."""
        import scripts.delete_agent as mod

        # Create two agents
        for name in ("agent_a", "agent_b"):
            (tmp_path / "agents" / name).mkdir(parents=True)
            (tmp_path / "tests" / name).mkdir(parents=True)

        registry = tmp_path / "agents" / "registry.py"
        registry.write_text(textwrap.dedent("""\
            from agents.agent_a.config import AgentAConfig  # noqa: E402
            from agents.agent_b.config import AgentBConfig  # noqa: E402

            REGISTRY = AgentRegistry(
                [
                    AgentRegistryEntry(
                        name="agent-a",
                        config_class=AgentAConfig,
                        factory=create_or_update_agent,
                    ),
                    AgentRegistryEntry(
                        name="agent-b",
                        config_class=AgentBConfig,
                        factory=create_or_update_agent,
                    ),
                ]
            )
        """))

        monkeypatch.setattr(mod, "AGENTS_DIR", tmp_path / "agents")
        monkeypatch.setattr(mod, "TESTS_DIR", tmp_path / "tests")
        monkeypatch.setattr(mod, "REGISTRY_PATH", registry)

        result = main(["--all", "--force", "--no-portal"])
        assert result == 0

        assert not (tmp_path / "agents" / "agent_a").exists()
        assert not (tmp_path / "agents" / "agent_b").exists()
        assert not (tmp_path / "tests" / "agent_a").exists()
        assert not (tmp_path / "tests" / "agent_b").exists()

    def test_delete_all_returns_1_when_no_agents(self, tmp_path, monkeypatch):
        """--all should fail if no agents are registered."""
        import scripts.delete_agent as mod

        registry = tmp_path / "registry.py"
        registry.write_text("REGISTRY = AgentRegistry([])")

        monkeypatch.setattr(mod, "REGISTRY_PATH", registry)

        result = main(["--all", "--force", "--no-portal"])
        assert result == 1

    def test_delete_all_cancellation(self, tmp_path, monkeypatch):
        """--all without --force should respect cancellation."""
        import scripts.delete_agent as mod

        registry = tmp_path / "registry.py"
        registry.write_text('name="some-agent"')
        (tmp_path / "agents" / "some_agent").mkdir(parents=True)

        monkeypatch.setattr(mod, "AGENTS_DIR", tmp_path / "agents")
        monkeypatch.setattr(mod, "TESTS_DIR", tmp_path / "tests")
        monkeypatch.setattr(mod, "REGISTRY_PATH", registry)
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = main(["--all"])
        assert result == 1
        # Agent dir should still exist
        assert (tmp_path / "agents" / "some_agent").exists()
