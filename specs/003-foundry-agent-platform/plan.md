# Implementation Plan: Foundry Agent Platform

**Branch**: `003-foundry-agent-platform` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/003-foundry-agent-platform/spec.md`

## Summary

Build a production-grade, multi-agent platform using the Azure AI Foundry Agent Service SDK (`azure-ai-projects`, Python 3.11+). Each agent is self-contained in its own folder with config, instructions, tools, and integration stubs, registered in a central registry, and deployable individually or together across dev/qa/prod via a CLI script and GitHub Actions. Infrastructure is provisioned declaratively via Terraform or Bicep (user's choice), with optional Foundry resource creation using the new CognitiveServices/AIServices model. Authentication uses `DefaultAzureCredential` everywhere and OIDC in CI/CD. Knowledge source (Azure AI Search) and GitHub OpenAPI integration are architecturally reserved via stubs but deferred.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: azure-ai-projects (AIProjectClient, AgentsClient, FunctionTool, ThreadMessage, Run, RunStatus), azure-identity (DefaultAzureCredential), pydantic-settings
**Storage**: N/A (stateless agents — Azure AI Foundry manages agent/thread state server-side)
**Testing**: pytest, pytest-asyncio; Black, isort, flake8 for code quality
**Target Platform**: Azure AI Foundry Agent Service (serverless — no containers, no AKS)
**Project Type**: Multi-agent platform (CLI + IaC + SDK integration)
**Performance Goals**: Agent run polling completes within 120s default timeout; deploy script handles N agents sequentially with per-agent error isolation
**Constraints**: No Docker/Kubernetes/Container Apps; DefaultAzureCredential only (no API keys); new Foundry resource model only (CognitiveServices/AIServices, never classic Hub+Project); all environment differences via config files only
**Scale/Scope**: 2+ agents initially, extensible to N; 3 environments (dev/qa/prod); 2 IaC paths (Terraform + Bicep)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I.1 | Python typed, linted, formatted | PASS | Black, isort, flake8 in test pipeline (FR-017); Python 3.11+ with type hints |
| I.2 | Code readable by unfamiliar dev | PASS | Self-contained agent folders, clear naming conventions, notebook onboarding |
| I.3 | Public function/class/module docstrings | PASS | Will be enforced during implementation; code quality tooling in CI |
| I.4 | No hardcoded secrets | PASS | DefaultAzureCredential everywhere (FR-006, FR-020); Key Vault for GitHub PAT (FR-009); no API keys |
| I.5 | Feature flags for incomplete capabilities | PASS | KNOWLEDGE_SOURCE_ENABLED, GITHUB_OPENAPI_ENABLED flags (FR-008, FR-009, FR-010) |
| II.1 | Declarative, version-controlled infra | PASS | Terraform + Bicep in repo (FR-011–FR-016) |
| II.2 | Environments structurally identical | PASS | Config-only differences via tfvars/bicepparam (FR-014) |
| II.3 | Same codebase, all environments | PASS | No environment-specific code forks — env vars and config files only |
| II.4 | No manual changes — everything via CI/CD | PASS | GitHub Actions deploy pipeline (FR-018–FR-021); prod requires approval gate |
| II.5 | Extensible without restructuring | PASS | Agent folder + registry pattern (FR-003, SC-002); integration stubs (FR-008–FR-010) |
| II.6 | Prefer managed Azure services | PASS | Serverless Foundry, managed Key Vault, managed AI Search |
| III.1 | Every assertable behaviour tested | PASS | Unit + integration test layers (FR-022–FR-025) |
| III.2 | Unit tests — no live credentials | PASS | SDK mocked (FR-022) |
| III.3 | Integration tests separated, skippable | PASS | `@pytest.mark.integration`, auto-skip when connection string unset (FR-025) |
| III.4 | No merge with failing tests | PASS | Test pipeline must pass before merge (FR-017) |
| III.5 | Tests are first-class code | PASS | Same quality standards, structured test directories |
| IV.1 | All deployments automated | PASS | GitHub Actions deploy pipeline (FR-018) |
| IV.2 | Prod requires human approval | PASS | GitHub Environment approval gate (FR-021) |
| IV.3 | Test suite runs before every deployment | PASS | Test stage precedes deploy stage in pipeline |
| IV.4 | Deployments idempotent | PASS | create_or_update_agent pattern (FR-002) |
| IV.5 | Short-lived tokens (OIDC) | PASS | Workload Identity Federation (FR-020) |
| IV.6 | Main always deployable | PASS | Test pipeline gates (FR-017), auto-deploy dev on push to main |
| IV.7 | Work on feature branches, PR to main | PASS | Standard workflow, test pipeline triggers on PR |
| IV.8 | PR requires review | PASS | Will be configured as branch protection rule |
| IV.9 | Descriptive commit messages | PASS | Convention-level; not enforced by tooling in scope |
| V.1 | Agents have version-controlled instructions | PASS | instructions.md per agent folder (FR-005) |
| V.2 | Agent changes via pipeline | PASS | Same CI/CD as code (FR-018–FR-021) |
| V.3 | Agents testable in isolation | PASS | Per-agent test markers (FR-024), per-agent deploy (FR-029) |
| V.4 | Works without knowledge sources | PASS | Knowledge integration is optional extension, default disabled (FR-008) |
| Doc.1 | Notebook-based onboarding | PASS | Two notebooks (FR-026–FR-028) |
| Doc.2 | READMEs current | PASS | README required with decision guide for Foundry modes |
| Doc.3 | Architecture decisions recorded | PASS | Spec clarifications section, plan research.md |
| Doc.4 | Notebooks for newcomers | PASS | Target audience: Python dev new to Foundry |
| Ext.1 | Integration points clearly marked | PASS | integrations/ folder per agent with stubs (FR-008, FR-009) |
| Ext.2 | Removing integration point = breaking change | PASS | Stubs reserved by contract |
| Ext.3 | Knowledge stub preserved | PASS | FR-008 maintains placeholder |
| Ext.4 | Knowledge configurable per env, no breakage | PASS | Per-agent env vars, defaults to disabled |
| Gov.1 | Constitution supersedes | PASS | No conflicts detected |
| Gov.4 | Complexity justified | PASS | Dual IaC paths justified by user choice requirement; dual integration stubs justified by spec |

**Gate result: PASS — all principles satisfied. Proceeding to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/003-foundry-agent-platform/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── agent-registry.md
│   ├── agent-factory.md
│   ├── deploy-script.md
│   └── cicd-pipeline.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
agents/
├── _base/
│   ├── __init__.py
│   ├── agent_factory.py        # Shared create_or_update_agent() logic
│   ├── client.py               # Singleton AIProjectClient initialisation
│   ├── config.py               # Base pydantic-settings config
│   ├── run.py                  # Thread-and-run lifecycle helper
│   └── tools/
│       └── __init__.py         # Shared tool utilities
├── <agent-name-1>/
│   ├── __init__.py
│   ├── config.py               # Extends base config
│   ├── instructions.md         # Versioned agent instructions
│   ├── tools/
│   │   ├── __init__.py
│   │   └── sample_tool.py
│   └── integrations/
│       ├── knowledge.py        # Knowledge source stub
│       └── github_openapi.py   # GitHub OpenAPI stub
├── <agent-name-2>/
│   └── ...                     # Same structure
└── registry.py                 # Agent registry

infra/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   └── envs/
│       ├── dev.tfvars
│       ├── qa.tfvars
│       └── prod.tfvars
└── bicep/
    ├── main.bicep
    ├── parameters/
    │   ├── dev.bicepparam
    │   ├── qa.bicepparam
    │   └── prod.bicepparam
    └── modules/
        ├── foundry-resource.bicep
        ├── foundry-project.bicep
        ├── keyvault.bicep
        └── ai-search.bicep

tests/
├── conftest.py                 # Root fixtures
├── _base/
│   ├── test_agent_factory.py
│   ├── test_client.py
│   └── test_config.py
├── <agent-name-1>/
│   ├── conftest.py             # Agent-specific fixtures
│   ├── test_agent_create.py
│   ├── test_agent_run.py
│   └── test_tools.py
└── <agent-name-2>/
    └── ...

notebooks/
├── 01_setup_and_connect.ipynb
└── 02_build_and_run_agent.ipynb

scripts/
└── deploy_agent.py             # CLI: --agent <name> or --all

.github/
└── workflows/
    ├── test.yml                # PR/push test pipeline
    └── deploy.yml              # Deploy pipeline with workflow_dispatch

.env.example
requirements.txt
requirements-dev.txt
README.md
pyproject.toml
```

**Structure Decision**: Custom multi-agent layout as specified in the feature spec. Not a standard single-project, web-app, or mobile pattern. The `agents/` directory is the primary code root with a shared `_base/` module and per-agent folders. Infrastructure lives in `infra/` with parallel Terraform and Bicep paths. Tests mirror the agents structure under `tests/`.

## Complexity Tracking

> No constitution violations detected — table not required.

## Post-Design Constitution Re-check

*Re-evaluated after Phase 1 design artifacts (data-model.md, contracts/, quickstart.md).*

| Principle | Post-Design Status | Notes |
|---|---|---|
| I.5 Feature flags for incomplete capabilities | PASS | IntegrationStub entity uses `KNOWLEDGE_SOURCE_ENABLED` / `GITHUB_OPENAPI_ENABLED` flags |
| II.5 Extensible without restructuring | PASS | Registry contract: new agent = one `AgentRegistryEntry` line; self-contained folder |
| III.1 Every assertable behaviour tested | PASS | All contract error conditions (ValueError, KeyError, FileNotFoundError) are testable |
| IV.4 Deployments idempotent | PASS | Agent factory contract explicitly guarantees idempotency via create-or-update |
| V.1 Version-controlled instructions | PASS | Data model: instructions loaded from `instructions.md` file per agent |
| Ext.1-3 Integration points marked & preserved | PASS | IntegrationStub entity with explicit contract; stubs return `None` when disabled |
| Gov.4 Complexity justified | PASS | No unnecessary abstractions introduced; dual IaC paths justified by spec requirement |

**Post-design gate: PASS — no new violations. Ready for `/speckit.tasks`.**
