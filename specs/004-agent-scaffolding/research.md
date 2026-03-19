# Research: Agent Scaffolding Automation

**Feature**: 004-agent-scaffolding  
**Date**: 2026-03-19  
**Status**: Complete (updated with R8)

## R1: Code Generation Approach

**Decision**: String templates using Python `textwrap.dedent` and f-strings  
**Rationale**: The agent file structures are simple and highly uniform. Both existing agents (`code_helper`, `doc_assistant`) are structurally identical — same files, same patterns, only names and placeholder content differ. Python string templates are sufficient, require no additional dependencies, and are easy to maintain and audit.  
**Alternatives considered**:
- Jinja2 templates: Adds external dependency (violates NFR-1); overkill for ~12 files with simple name substitution
- AST manipulation: Over-engineered for generating boilerplate; harder to read and maintain
- Cookiecutter/Copier: Adds external dependency; introduces tool-specific abstractions unnecessary for this project's scale

## R2: Registry Modification Strategy

**Decision**: Text-based insertion using regex pattern matching on `agents/registry.py`  
**Rationale**: The registry file has a predictable structure — imports at the bottom (with `# noqa: E402`), followed by `REGISTRY = AgentRegistry([...])`. The script will:
1. Read the file content
2. Insert a new import line after the last existing config import
3. Insert a new `AgentRegistryEntry(...)` block before the closing `])` of the REGISTRY list
4. Write the file back

This is safe because:
- The file format is consistent and well-structured
- The patterns to match are unique (closing `])` of REGISTRY, import block)
- The script validates the file can be parsed before writing
- A backup is not needed since the file is version-controlled

**Alternatives considered**:
- AST-based modification (via `ast` module): More robust but significantly more complex; loses formatting and comments; not worth it for appending 2 blocks of text
- Requiring manual registry update: Defeats the purpose of automation; error-prone

## R3: YAML Input Schema Design

**Decision**: Simple flat YAML with required `name` and optional `model` fields  
**Rationale**: Matches the CLI arguments exactly. Keeps the schema simple for v1. Can be extended later with additional fields (instructions template, tool definitions) without breaking changes.

```yaml
# Example: agent-config.yaml
name: my-agent
model: gpt-4o  # optional, default: gpt-4o
```

**Alternatives considered**:
- JSON: Less human-friendly for manual editing
- TOML: Not in standard library (Python 3.11 has `tomllib` for reading but no writer); YAML via PyYAML is also not stdlib, but can be handled with simple key-value parsing if PyYAML is unavailable
- Note: PyYAML is not in requirements.txt. The script will use a simple key-value parser for the YAML subset needed (flat key: value pairs), avoiding a new dependency. If full YAML is needed later, PyYAML can be added.

## R4: Agent Name Conventions

**Decision**: Accept kebab-case input (e.g., `my-agent`), derive snake_case for Python identifiers (e.g., `my_agent`), and PascalCase for class names (e.g., `MyAgentConfig`)  
**Rationale**: This matches existing conventions exactly:
- `code-helper` → `code_helper` (directory/module) → `CodeHelperConfig` (class)
- `doc-assistant` → `doc_assistant` (directory/module) → `DocAssistantConfig` (class)

**Validation rules**:
- Must match pattern `^[a-z][a-z0-9]*(-[a-z0-9]+)*$` (lowercase kebab-case)
- Must not conflict with existing agent names in registry
- Must not conflict with Python reserved words or existing module names

## R5: GitHub Actions Workflow Design

**Decision**: Manual `workflow_dispatch` trigger with `agent_name` and `model` inputs. Creates branch, runs scaffolding script, commits, opens PR.  
**Rationale**: Follows the existing workflow patterns in the project (deploy.yml uses `workflow_dispatch`). Manual trigger is appropriate because agent creation is an infrequent, deliberate action.

**Workflow steps**:
1. Checkout repository
2. Set up Python
3. Run `python scripts/create_agent.py --name ${{ inputs.agent_name }} --model ${{ inputs.model }}`
4. Create branch `scaffold/${{ inputs.agent_name }}`
5. Commit generated files
6. Open PR against `main` using `gh pr create`

**Auth**: Uses `GITHUB_TOKEN` (built-in, no additional secrets needed). The `contents: write` and `pull-requests: write` permissions are required.

## R6: Idempotency and Safety Guards

**Decision**: Fail-fast if agent directory already exists. No `--force` flag in v1.  
**Rationale**: Overwriting existing agent code is destructive and dangerous. The correct workflow for regenerating is to delete the old agent first (an explicit, conscious action). The constitution requires that complexity must be justified — a `--force` flag adds complexity for a rare edge case.

**Checks performed before any file generation**:
1. Agent directory `agents/<name>/` must not exist
2. Test directory `tests/<name>/` must not exist
3. Agent name must not already be in registry
4. Agent name must pass validation (kebab-case, no reserved words)

## R7: Generated Test Structure

**Decision**: Generate both unit test stubs and integration test stubs matching existing patterns  
**Rationale**: Both `code_helper` and `doc_assistant` have test directories. The generated tests should be immediately runnable (unit tests pass, integration tests skip without credentials).

**Generated test files**:
- `conftest.py`: Config fixture with MonkeyPatch for env vars, module-level pytestmark
- `test_tools.py`: Unit tests for the sample tool function
- `test_agent_create.py`: Integration test stub for agent creation lifecycle
- `test_agent_run.py`: Integration test stub for agent run lifecycle

## R8: Documentation Strategy — README + Dedicated Guide

**Decision**: Two-tier documentation — concise README section + dedicated `docs/scaffolding-guide.md`  
**Rationale**: The constitution mandates that READMEs MUST be kept current (outdated docs = bug). The current README "Adding a New Agent" section describes only the manual 3-step process. Adding CLI/YAML/GHA details inline would bloat it. Instead:

1. **README update**: Expand the "Adding a New Agent" section to briefly describe all three creation methods (manual, CLI, YAML) and link to the detailed guide. Add the GitHub Actions workflow to the CI/CD table.
2. **`docs/scaffolding-guide.md`**: Comprehensive guide covering setup, all usage modes, YAML format, generated file breakdown, customisation after scaffolding, FAQ, and troubleshooting.

**README changes** (specific):
- "Adding a New Agent" section: Replace the 3-step manual instructions with a brief overview of all methods + link to `docs/scaffolding-guide.md`
- CI/CD table: Add `create-agent.yml` row
- Architecture tree: Add `scripts/create_agent.py` and `docs/` entries

**`docs/scaffolding-guide.md` structure**:
1. **Overview** — What the scaffolding tool does
2. **Prerequisites** — Python 3.11+, repo cloned
3. **Usage** — CLI mode, YAML mode, GitHub Actions mode
4. **Generated Files** — Directory tree + what each file does
5. **Customisation** — What to edit after scaffolding (instructions, tools, config)
6. **YAML Input Reference** — Schema, examples, validation rules
7. **FAQ** — Common questions (how to rename, how to delete, how to add tools)
8. **Troubleshooting** — Error messages and resolutions

**Alternatives considered**:
- Docs in README only: Would make README too long; violates clarity principle
- Docs in specs/ only: Specs are design-time docs, not user-facing; not discoverable by new developers
- Separate wiki or external docs: Over-engineered for a single CLI tool; keeps docs out of version control
- Notebook-based guide: Constitution recommends notebooks for onboarding to Azure AI Foundry features, but scaffolding is a developer tool, not an Azure capability demo — a Markdown guide is more appropriate as the *primary* reference. However, the constitution's MUST language for notebook walkthroughs requires a complementary notebook (`notebooks/03_scaffold_agent.ipynb`) demonstrating the CLI workflow alongside the written guide
