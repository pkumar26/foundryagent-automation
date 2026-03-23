# Implementation Plan: Migrate to New Foundry SDK (azure-ai-projects v2)

**Branch**: `005-migrate-to-new-foundry` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-migrate-to-new-foundry/spec.md`

## Summary

Migrate the foundryagent-automation codebase from the legacy `azure-ai-agents` SDK (`AgentsClient`, threads/runs model) to the GA `azure-ai-projects` v2.x SDK (`AIProjectClient`, `create_version`, OpenAI conversations/responses model). This touches the client singleton, agent factory, run lifecycle, tool definitions, configuration, all tests, notebooks, scripts, and documentation.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `azure-ai-projects>=2.0.0` (replaces `azure-ai-agents`), `azure-identity>=1.15.0`, `pydantic-settings>=2.0.0`, `openai` (transitive via azure-ai-projects v2)
**Storage**: N/A (serverless agents in Azure AI Foundry)
**Testing**: pytest with markers (`integration`, `code_helper`, `doc_assistant`); unit tests mock SDK; integration tests require Azure credentials
**Target Platform**: Linux/macOS/Windows (developer workstations + CI/CD)
**Project Type**: SDK automation platform (library + CLI scripts + notebooks)
**Performance Goals**: N/A (not a server — deploy/invoke latency governed by Azure)
**Constraints**: Must remain runnable without Azure credentials for unit tests; all existing agent functionality preserved
**Scale/Scope**: 2 agents (code-helper, doc-assistant), ~15 source files, ~15 test files, 3 notebooks, 2 scripts, 3 docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Coding Standards — typed, linted, formatted | PASS | No new untyped code; existing type annotations preserved |
| I. Coding Standards — docstrings on public API | PASS | All modified public functions retain/update docstrings |
| I. Coding Standards — no hardcoded secrets | PASS | Endpoint sourced from env var `AZURE_AI_PROJECT_ENDPOINT` |
| II. Architecture — declarative infra | PASS | No infra changes needed |
| II. Architecture — extensibility without restructure | PASS | Same self-contained agent pattern preserved |
| III. Testing — assertable behaviour has tests | PASS | All updated code has corresponding test updates |
| III. Testing — unit tests without live credentials | PASS | Mocked SDK classes updated to new API surface |
| III. Testing — integration tests clearly separated | PASS | Marker strategy unchanged |
| IV. CI/CD — idempotent deployments | PASS | create-or-update pattern preserved via create_version |
| V. AI Agent Governance — version-controlled instructions | PASS | Instructions remain in markdown files |
| V. AI Agent Governance — testable in isolation | PASS | Mock-based unit tests continue to work |
| Documentation — notebook walkthroughs | PASS | All 3 notebooks updated |
| Extensibility — knowledge stub preserved | PASS | Integration stubs remain, just import paths change |

**Gate Result: PASS** — No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/005-migrate-to-new-foundry/
├── plan.md              # This file
├── research.md          # Phase 0: SDK migration decisions
├── data-model.md        # Phase 1: Entity/config changes
├── quickstart.md        # Phase 1: Migration steps
├── contracts/           # Phase 1: Updated API contracts
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
agents/
├── __init__.py
├── registry.py                    # UNCHANGED (no direct SDK references)
├── _base/
│   ├── __init__.py
│   ├── client.py                  # CHANGED: AgentsClient → AIProjectClient singleton
│   ├── config.py                  # CHANGED: env var rename
│   ├── agent_factory.py           # CHANGED: create_agent → create_version
│   ├── run.py                     # CHANGED: threads/runs → conversations/responses
│   ├── tools/
│   │   ├── __init__.py            # CHANGED: FunctionTool wrapping
│   │   └── __pycache__/
│   └── integrations/
│       └── __init__.py
├── code_helper/
│   ├── config.py                  # UNCHANGED (inherits from FoundryBaseConfig)
│   ├── instructions.md            # UNCHANGED
│   ├── tools/
│   │   ├── __init__.py
│   │   └── sample_tool.py         # CHANGED: tool schema format
│   └── integrations/
│       └── knowledge.py           # UNCHANGED (stub)
└── doc_assistant/
    ├── config.py                  # UNCHANGED (inherits from FoundryBaseConfig)
    ├── instructions.md            # UNCHANGED
    ├── tools/
    │   ├── __init__.py
    │   └── sample_tool.py         # CHANGED: tool schema format
    └── integrations/
        └── knowledge.py           # UNCHANGED (stub)

tests/
├── conftest.py                    # CHANGED: mock AIProjectClient
├── _base/
│   ├── test_client.py             # CHANGED: AIProjectClient tests
│   ├── test_config.py             # CHANGED: new env var
│   ├── test_agent_factory.py      # CHANGED: create_version mocks
│   └── test_run.py                # CHANGED: conversations/responses mocks
├── code_helper/
│   ├── conftest.py                # CHANGED: config fixture
│   ├── test_tools.py              # UNCHANGED (tests validate TOOLS exports, not schema internals)
│   ├── test_agent_create.py       # CHANGED: integration test
│   └── test_agent_run.py          # CHANGED: integration test
└── doc_assistant/
    ├── conftest.py
    ├── test_tools.py              # UNCHANGED (tests validate TOOLS exports, not schema internals)
    ├── test_agent_create.py
    └── test_agent_run.py
└── scaffolding/
    └── test_create_agent.py         # CHANGED: updated template assertions

scripts/
├── deploy_agent.py                # UNCHANGED (factory abstraction handles migration)
└── create_agent.py                # CHANGED: generated templates

notebooks/
├── 01_setup_and_connect.ipynb     # CHANGED: AIProjectClient
├── 02_build_and_run_agent.ipynb   # CHANGED: conversations/responses
└── 03_scaffold_agent.ipynb        # CHANGED: updated examples

docs/
├── custom-tools-guide.md          # CHANGED: new tool schema
├── infrastructure-guide.md        # CHANGED: env var name
└── scaffolding-guide.md           # CHANGED: new SDK references

pyproject.toml                     # CHANGED: dependency versions
requirements.txt                   # CHANGED: dependency versions
requirements-dev.txt               # UNCHANGED
.env.example                       # CHANGED: env var name
README.md                          # CHANGED: badges + SDK references
```

**Structure Decision**: Existing project structure retained. This migration is in-place — same files, updated implementations. No new modules or structural changes needed.

## Complexity Tracking

> No Constitution Check violations — this section is empty.
