# Data Model: Agent Scaffolding Automation

**Feature**: 004-agent-scaffolding  
**Date**: 2026-03-19

## Entities

### AgentDefinition

The input model representing an agent to be scaffolded. Parsed from CLI arguments or YAML input file.

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `name` | `str` | Yes | — | Kebab-case: `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`; max 50 chars; not a Python reserved word; not an existing agent name |
| `model` | `str` | No | `"gpt-4o"` | Non-empty string |

**Derived fields** (computed, not stored):
| Derived Field | Source | Example |
|---------------|--------|---------|
| `module_name` | `name.replace("-", "_")` | `my_agent` |
| `class_prefix` | PascalCase of `name` | `MyAgent` |
| `config_class_name` | `class_prefix + "Config"` | `MyAgentConfig` |
| `instructions_path` | `f"agents/{module_name}/instructions.md"` | `agents/my_agent/instructions.md` |
| `agent_dir` | `Path("agents") / module_name` | `agents/my_agent/` |
| `test_dir` | `Path("tests") / module_name` | `tests/my_agent/` |
| `agent_display_name` | `name.replace("-", " ").title()` | `My Agent` |

### GeneratedFileManifest

The output model representing all files created during scaffolding. Used for reporting and validation.

| Field | Type | Description |
|-------|------|-------------|
| `agent_dir` | `Path` | Root agent directory created |
| `test_dir` | `Path` | Root test directory created |
| `files_created` | `list[Path]` | All files generated |
| `registry_modified` | `bool` | Whether registry.py was updated |

## File Generation Map

Each scaffolded agent produces the following files:

| Generated File | Template Source | Key Substitutions |
|----------------|---------------|-------------------|
| `agents/{mod}/__init__.py` | Empty file | — |
| `agents/{mod}/config.py` | Config template | `{class_prefix}Config`, `{agent_name}`, `{model}`, `{instructions_path}` |
| `agents/{mod}/instructions.md` | Instructions template | `{agent_display_name}` |
| `agents/{mod}/tools/__init__.py` | Tools init template | `{mod}` |
| `agents/{mod}/tools/sample_tool.py` | Sample tool template | `{agent_display_name}` |
| `agents/{mod}/integrations/__init__.py` | Empty file | — |
| `agents/{mod}/integrations/github_openapi.py` | OpenAPI stub template | `{mod}` |
| `agents/{mod}/integrations/knowledge.py` | Knowledge stub template | `{mod}` |
| `tests/{mod}/__init__.py` | Empty file | — |
| `tests/{mod}/conftest.py` | Test conftest template | `{config_class_name}`, `{mod}` |
| `tests/{mod}/test_tools.py` | Test tools template | `{mod}`, sample function name |
| `tests/{mod}/test_agent_create.py` | Integration test template | `{agent_name}`, `{mod}` |
| `tests/{mod}/test_agent_run.py` | Integration test template | `{agent_name}`, `{mod}` |

Where `{mod}` = `module_name` (snake_case).

## Registry Modification

The script modifies `agents/registry.py` by:

1. **Adding import** after the last `from agents.*.config import *Config` line:
   ```python
   from agents.{module_name}.config import {ConfigClassName}  # noqa: E402
   ```

2. **Adding entry** before the closing `]` of the REGISTRY list:
   ```python
           AgentRegistryEntry(
               name="{agent-name}",
               config_class={ConfigClassName},
               factory=create_or_update_agent,
           ),
   ```

## State Transitions

The scaffolding process follows a linear state machine:

```
VALIDATE → GENERATE_AGENT_DIR → GENERATE_TEST_DIR → UPDATE_REGISTRY → REPORT
    │              │                     │                  │             │
    ▼              ▼                     ▼                  ▼             ▼
  Fail if       Create dirs        Create dirs         Modify         Print
  invalid       + files            + files            registry.py    summary
```

**Error handling**: If any step fails, no partial cleanup is performed (files are version-controlled, easy to revert via `git checkout`). The script exits with a non-zero code and a descriptive error message.

## Documentation Artifacts

The feature produces three documentation deliverables outside the `specs/` directory:

### README.md Updates

| Section | Change Type | Description |
|---------|-------------|-------------|
| "Adding a New Agent" | **Replace** | Expand from 3-step manual to multi-method overview (manual, CLI, YAML, GHA) with link to detailed guide |
| CI/CD table | **Append** | Add `create-agent.yml` row for scaffolding workflow |
| Architecture tree | **Append** | Add `scripts/create_agent.py` and `docs/` to tree diagram |

### docs/scaffolding-guide.md (New File)

| Section | Content |
|---------|---------|
| Overview | What the scaffolding tool does, why it exists |
| Prerequisites | Python 3.11+, repo cloned, venv activated |
| CLI Usage | `--name`, `--model` flags with examples |
| YAML Usage | `--from-file` with schema reference and example |
| GitHub Actions | How to trigger the `create-agent.yml` workflow |
| Generated Files | Full tree + description of each file's purpose |
| Customisation | What to edit after scaffolding (instructions, tools, config, tests) |
| YAML Input Reference | Field-by-field schema with types, defaults, validation |
| FAQ | Common questions: renaming agents, deleting agents, adding tools, changing models |
| Troubleshooting | Error→cause→resolution table for all validation errors |

### notebooks/03_scaffold_agent.ipynb (New File)

| Section | Content |
|---------|--------|
| Setup | Verify Python version and repo state |
| Scaffold | Run `create_agent.py --name demo-agent` and inspect output |
| Verify | List generated files and check registry |
| Test | Run `pytest tests/demo_agent/ -v` |
| Deploy | Show deploy command (informational — requires Azure credentials) |
