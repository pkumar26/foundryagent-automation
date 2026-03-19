# Implementation Plan: Agent Scaffolding Automation

**Branch**: `004-agent-scaffolding` | **Date**: 2026-03-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-agent-scaffolding/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add an automated agent scaffolding system to the FoundryAgent Automation platform. A CLI script (`scripts/create_agent.py`) generates all required directories, configuration, instructions, tools, integration stubs, test stubs, and registry entries for a new agent — matching existing agent patterns exactly. Supports interactive CLI (`--name`/`--model`), non-interactive YAML input (`--from-file`), and GitHub Actions workflow automation. Includes updated README and a dedicated scaffolding guide with setup, usage, FAQ, and troubleshooting. No new external dependencies required.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Python standard library only (argparse, pathlib, textwrap, re); pydantic-settings (existing, for generated config classes)  
**Storage**: Filesystem — generates Python source files and Markdown  
**Testing**: pytest (existing)  
**Target Platform**: Linux/macOS/Windows (developer workstations, GitHub Actions runners)  
**Project Type**: CLI tool (developer tooling, code generation)  
**Performance Goals**: < 2s execution for single agent scaffolding  
**Constraints**: No new external dependencies; generated code must pass existing linting (black, isort); must not modify existing agent code  
**Scale/Scope**: Generates ~13 files per agent across 2 directories (agents/, tests/); 1 doc file + README update

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Coding Standards — typed, linted, formatted | ✅ PASS | Script will be typed Python; generated code follows existing patterns |
| I. Coding Standards — docstrings on public API | ✅ PASS | All public functions will have docstrings |
| I. Coding Standards — no hardcoded secrets | ✅ PASS | No secrets involved in scaffolding |
| II. Architecture — declarative, version-controlled infra | ✅ N/A | No infrastructure changes |
| II. Architecture — extensibility without restructuring | ✅ PASS | New agents added by extension, not modification of core code |
| II. Architecture — no manual changes, everything through CI/CD | ✅ PASS | GitHub Actions workflow provided for CI-driven scaffolding |
| III. Testing — every assertable behaviour has a test | ✅ PASS | Tests for the scaffolding script itself + generated test stubs |
| III. Testing — unit tests require no Azure credentials | ✅ PASS | Scaffolding is purely filesystem operations |
| IV. CI/CD — automated deployments | ✅ PASS | GHA workflow creates PR with scaffolded agent |
| IV. CI/CD — OIDC, no long-lived secrets | ✅ PASS | GHA workflow uses `GITHUB_TOKEN` (built-in) |
| V. AI Agent Governance — explicit, version-controlled instructions | ✅ PASS | Generated instructions.md is version-controlled |
| V. AI Agent Governance — agent changes treated as code changes | ✅ PASS | All changes go through PR review |
| Documentation — READMEs MUST be kept current | ✅ PASS | README updated with scaffolding section; dedicated guide created |
| Documentation — architecture decisions recorded | ✅ PASS | Spec + plan + research documents all decisions |
| Extensibility Contract — integration points preserved | ✅ PASS | Generated stubs preserve knowledge/MCP integration points |
| Documentation — notebook walkthrough for onboarding | ✅ PASS | `notebooks/03_scaffold_agent.ipynb` demonstrates scaffolding CLI |

**Gate Status**: ✅ PASS — All mandatory principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/004-agent-scaffolding/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/
└── create_agent.py          # CLI scaffolding script (new)

agents/
├── registry.py              # Modified — new entry appended per scaffolded agent
└── <new_agent>/             # Generated per agent
    ├── __init__.py
    ├── config.py
    ├── instructions.md
    ├── integrations/
    │   ├── __init__.py
    │   ├── github_mcp.py
    │   └── knowledge.py
    └── tools/
        ├── __init__.py
        └── sample_tool.py

tests/
├── <new_agent>/             # Generated per agent
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_tools.py
│   ├── test_agent_create.py
│   └── test_agent_run.py
└── scaffolding/             # Tests for the scaffolding script itself
    ├── __init__.py
    └── test_create_agent.py

docs/
└── scaffolding-guide.md     # Setup, usage, FAQ, troubleshooting (new)

README.md                    # Updated — "Adding a New Agent" section expanded

notebooks/
└── 03_scaffold_agent.ipynb   # Walkthrough: scaffold + customise an agent (new)

.github/
└── workflows/
    └── create-agent.yml     # GitHub Actions workflow (new)
```

**Structure Decision**: Follows existing repository layout. New `docs/` directory introduced for the dedicated scaffolding guide — keeps README concise while providing depth where needed. All generated agent code follows the exact patterns of `code_helper` and `doc_assistant`. No restructuring of existing code.

## Complexity Tracking

> No violations — no justification needed.

## Constitution Re-Check (Post-Design)

| Principle | Status | Post-Design Notes |
|-----------|--------|-------------------|
| I. Coding Standards — typed, linted, formatted | ✅ PASS | Script uses type hints; generated code follows black/isort conventions |
| I. Coding Standards — docstrings on public API | ✅ PASS | All public functions in script have docstrings; generated code includes docstrings |
| I. Coding Standards — no hardcoded secrets | ✅ PASS | No secrets in scaffolding; GHA uses built-in GITHUB_TOKEN |
| II. Architecture — extensibility | ✅ PASS | New agents added purely by extension; no modification to base or existing agent code |
| II. Architecture — no manual changes | ✅ PASS | GHA workflow automates the process end-to-end |
| III. Testing — assertable behaviour tested | ✅ PASS | Scaffolding script has its own test suite; generated agents get test stubs |
| III. Testing — no Azure credentials for unit tests | ✅ PASS | All scaffolding tests are filesystem-only |
| IV. CI/CD — automated | ✅ PASS | GHA workflow with `workflow_dispatch` |
| IV. CI/CD — OIDC, no long-lived secrets | ✅ PASS | Only uses GITHUB_TOKEN |
| V. AI Agent Governance — version-controlled instructions | ✅ PASS | Generated instructions.md checked into git |
| Documentation — READMEs MUST be kept current | ✅ PASS | README "Adding a New Agent" updated; CI/CD table updated; architecture tree updated |
| Documentation — outdated docs = bug | ✅ PASS | Dedicated `docs/scaffolding-guide.md` with FAQ + troubleshooting keeps docs comprehensive |
| Extensibility Contract — integration points preserved | ✅ PASS | Generated stubs for knowledge + github_mcp match existing patterns |
| Documentation — notebook walkthrough for onboarding | ✅ PASS | `notebooks/03_scaffold_agent.ipynb` walks through scaffold + customise + deploy |

**Post-Design Gate Status**: ✅ PASS — All principles satisfied. Documentation requirement fully addressed with README update + dedicated guide + onboarding notebook.

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Feature Spec | `specs/004-agent-scaffolding/spec.md` | ✅ Created |
| Research | `specs/004-agent-scaffolding/research.md` | ✅ Created |
| Data Model | `specs/004-agent-scaffolding/data-model.md` | ✅ Created |
| Quickstart | `specs/004-agent-scaffolding/quickstart.md` | ✅ Created |
| CLI Contract | `specs/004-agent-scaffolding/contracts/cli-create-agent.md` | ✅ Created |
| GHA Contract | `specs/004-agent-scaffolding/contracts/gha-create-agent.md` | ✅ Created |
| Documentation Contract | `specs/004-agent-scaffolding/contracts/documentation.md` | ✅ Created |
