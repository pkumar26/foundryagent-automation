# Feature Specification: Agent Scaffolding Automation

**Feature Branch**: `004-agent-scaffolding`  
**Created**: 2026-03-19  
**Status**: Draft  
**Input**: User description: "Create an automated scaffolding process for this codebase to generate new agents. At present there is no CLI command, template, input file, or interactive wizard. The workflow is fully manual. Add a script (`python scripts/create_agent.py --name my-agent`) that generates the necessary directories, configuration files, tools, instructions, integration stubs, test stubs, and registry entries for a new agent based on user input or predefined templates. Optionally support a YAML input file for non-interactive use and a GitHub Actions workflow for automated agent creation via CI."

## Clarifications

### Session 2026-03-19

- Q: Should the scaffolding script modify the existing `agents/registry.py` to add the new agent entry automatically? → A: Yes. The script should append a new `AgentRegistryEntry` to the `REGISTRY` list in `agents/registry.py`, including the import for the new config class. The modification must be safe — it must not corrupt existing entries.
- Q: What input parameters should the scaffolding script accept? → A: At minimum: `--name` (agent name, e.g., `my-agent`), `--model` (model name, default `gpt-4o`). Optionally: `--from-file` (path to a YAML config file for non-interactive batch creation).
- Q: Should the script generate test files? → A: Yes. It should generate test stubs under `tests/<agent_name>/` mirroring the existing test patterns (conftest, test_tools, test_agent_create, test_agent_run).
- Q: Should the generated code be immediately deployable without further edits? → A: The generated agent should be deployable out of the box with a sample tool and default instructions. Developers can then customise the instructions, tools, and config as needed.
- Q: Should there be a GitHub Actions workflow for automated agent creation? → A: Yes. A workflow that accepts agent name and model as inputs, runs the scaffolding script, and opens a pull request with the generated files.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Scaffold a New Agent via CLI (Priority: P1)

A developer wants to add a new agent to the platform. They run `python scripts/create_agent.py --name my-agent` and the script generates all required files (config, instructions, tools, integrations, tests) and registers the agent in the registry.

**Why this priority**: This is the core capability — manual agent creation is error-prone and time-consuming. Automating it improves developer experience and ensures consistency.

**Acceptance Scenarios**:

1. **Given** a developer runs `python scripts/create_agent.py --name my-agent`, **When** the script completes, **Then** the directory `agents/my_agent/` exists with `__init__.py`, `config.py`, `instructions.md`, `tools/__init__.py`, `tools/sample_tool.py`, `integrations/__init__.py`, `integrations/github_openapi.py`, `integrations/knowledge.py`.
2. **Given** the scaffolding script has completed, **When** the developer inspects `agents/registry.py`, **Then** it contains a new `AgentRegistryEntry` for `my-agent` with the correct config class and factory.
3. **Given** the scaffolding script has completed, **When** the developer inspects `tests/my_agent/`, **Then** it contains `__init__.py`, `conftest.py`, `test_tools.py`, `test_agent_create.py`, and `test_agent_run.py`.
4. **Given** an agent with the same name already exists, **When** the developer runs the script again, **Then** the script fails with a clear error message and does not overwrite existing files.

### User Story 2 — Scaffold Agent from YAML Input File (Priority: P2)

A developer or CI pipeline wants to create an agent non-interactively using a YAML configuration file. They run `python scripts/create_agent.py --from-file agent-config.yaml` and the script reads the agent definition from the file.

**Why this priority**: Non-interactive creation enables CI/CD automation and batch agent creation, which is essential for teams managing multiple agents.

**Acceptance Scenarios**:

1. **Given** a valid YAML file with `name: my-agent` and `model: gpt-4o`, **When** the developer runs `python scripts/create_agent.py --from-file agent-config.yaml`, **Then** the same files are generated as in User Story 1.
2. **Given** an invalid YAML file (e.g., missing `name`), **When** the script is run, **Then** it fails with a clear validation error.

### User Story 3 — GitHub Actions Workflow for Agent Creation (Priority: P3)

A team wants to automate agent creation via GitHub Actions. A workflow is triggered manually with agent name and model as inputs. It runs the scaffolding script and opens a pull request with the generated files.

**Why this priority**: Automation via CI ensures that agent creation follows the team's branching and review process, and enables non-developer team members to trigger agent creation.

**Acceptance Scenarios**:

1. **Given** a manual workflow dispatch with inputs `agent_name=my-agent` and `model=gpt-4o`, **When** the workflow runs, **Then** it creates a new branch, runs the scaffolding script, commits the generated files, and opens a pull request.
2. **Given** the pull request is opened, **When** a reviewer inspects it, **Then** it contains all scaffolded files and the registry update.

### User Story 4 — Updated README and Dedicated Scaffolding Guide (Priority: P2)

A developer new to the project wants to understand both the manual and automated ways to add a new agent. The README provides a concise overview with a link to a detailed scaffolding guide. The dedicated guide (`docs/scaffolding-guide.md`) covers setup, usage, YAML input format, generated file structure, customisation after scaffolding, FAQ, and troubleshooting.

**Why this priority**: The constitution mandates that READMEs MUST be kept current and that outdated documentation is treated as a bug. Adding a CLI tool without documenting it violates this principle.

**Acceptance Scenarios**:

1. **Given** the scaffolding feature is added, **When** a developer reads the README's "Adding a New Agent" section, **Then** it describes both the manual and automated (CLI/YAML/GHA) approaches and links to the detailed guide.
2. **Given** a developer opens `docs/scaffolding-guide.md`, **When** they read it, **Then** it includes: setup prerequisites, CLI usage examples, YAML input format, generated file structure, customisation instructions, FAQ, and troubleshooting.
3. **Given** a developer encounters a common error (e.g., duplicate agent name, invalid name format), **When** they check the troubleshooting section, **Then** they find the error message and resolution steps.
4. **Given** a developer opens `notebooks/03_scaffold_agent.ipynb`, **When** they run the notebook cells, **Then** they can scaffold a sample agent, verify the generated files, run the generated tests, and see the deploy command — completing the onboarding walkthrough.

## Requirements

### Functional Requirements

- FR-1: CLI script at `scripts/create_agent.py` that accepts `--name` and optional `--model` arguments.
- FR-2: Generated agent directory structure matches existing agent patterns exactly.
- FR-3: Generated config class extends `FoundryBaseConfig` with correct defaults.
- FR-4: Generated instructions file includes a placeholder template.
- FR-5: Generated tools module includes a sample tool following existing patterns.
- FR-6: Generated integration stubs (knowledge, github_openapi) follow existing patterns.
- FR-7: Generated test stubs follow existing test patterns.
- FR-8: Registry update appends new entry without corrupting existing entries.
- FR-9: Idempotency guard — refuse to overwrite existing agent directories.
- FR-10: YAML input file support via `--from-file` flag.
- FR-11: GitHub Actions workflow for automated scaffolding and PR creation.
- FR-12: README "Adding a New Agent" section updated to document CLI, YAML, and GHA approaches with link to detailed guide.
- FR-13: Dedicated `docs/scaffolding-guide.md` with setup, usage, YAML format, generated structure, customisation, FAQ, and troubleshooting sections.
- FR-14: Notebook-based walkthrough (`notebooks/03_scaffold_agent.ipynb`) demonstrating CLI scaffolding usage for developer onboarding.

### Non-Functional Requirements

- NFR-1: No new external dependencies — use only Python standard library and existing project dependencies.
- NFR-2: Generated code passes existing linting and formatting checks.
- NFR-3: Script provides clear, actionable error messages for all failure modes.
- NFR-4: Script completes in under 2 seconds for a single agent.
