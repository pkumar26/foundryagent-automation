# Tasks: Foundry Agent Platform

**Input**: Design documents from `/specs/003-foundry-agent-platform/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are explicitly requested (User Story 6, FR-022–FR-025). Test tasks are included in Phase 8 (US6).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Paths follow the custom multi-agent layout from plan.md
- Agent code: `agents/` at repository root
- Infrastructure: `infra/terraform/` and `infra/bicep/`
- Tests: `tests/` mirroring `agents/` structure
- Scripts: `scripts/`
- Notebooks: `notebooks/`
- CI/CD: `.github/workflows/`

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create the project skeleton, dependency files, and tooling configuration

- [X] T001 Create full project directory structure with all __init__.py files per plan.md (agents/_base/, agents/_base/tools/, agents/<agent-1>/, agents/<agent-1>/tools/, agents/<agent-1>/integrations/, agents/<agent-2>/, agents/<agent-2>/tools/, agents/<agent-2>/integrations/, infra/terraform/, infra/terraform/envs/, infra/bicep/, infra/bicep/modules/, infra/bicep/parameters/, tests/_base/, tests/<agent-1>/, tests/<agent-2>/, notebooks/, scripts/, .github/workflows/)
- [X] T002 [P] Initialize Python project with pyproject.toml (metadata, Black/isort config) and dependency files requirements.txt (azure-ai-projects, azure-identity, pydantic-settings) and requirements-dev.txt (pytest, pytest-asyncio, black, isort, flake8) at project root
- [X] T003 [P] Create .env.example listing all environment variables (FOUNDRY_PROJECT_CONNECTION_STRING, ENVIRONMENT, AZURE_KEY_VAULT_NAME, AGENT_NAME, AGENT_MODEL, KNOWLEDGE_SOURCE_ENABLED, GITHUB_OPENAPI_ENABLED, AZURE_AI_SEARCH_ENDPOINT, AZURE_AI_SEARCH_INDEX_NAME, GITHUB_OPENAPI_ENDPOINT, GITHUB_OPENAPI_TOKEN_SECRET_NAME) at project root
- [X] T004 [P] Create .flake8 configuration file and .gitignore (Python, .env, __pycache__, .venv, *.tfstate, .terraform/, .idea/, .vscode/) at project root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core modules that ALL user stories depend on — base config, client, registry, and agent factory

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement FoundryBaseConfig using pydantic-settings BaseSettings with fields (foundry_project_connection_string, environment, azure_key_vault_name) and .env file support in agents/_base/config.py
- [X] T006 [P] Implement singleton AIProjectClient initialisation using DefaultAzureCredential and connection string from config in agents/_base/client.py
- [X] T007 Implement AgentRegistryEntry dataclass and AgentRegistry class with list_agents(), get_agent(name), validate() per registry contract in agents/registry.py
- [X] T008 Implement create_or_update_agent() with idempotent create-or-update pattern (list agents → find by name → create or update), instructions file loading, tool collection, and conditional integration tool appending per factory contract in agents/_base/agent_factory.py
- [X] T009 [P] Create shared tool utilities module with FunctionTool helper in agents/_base/tools/__init__.py

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Connect to Existing Foundry and Deploy First Agent (Priority: P1) 🎯 MVP

**Goal**: A developer clones the repo, sets a connection string, deploys one agent, and verifies it responds to a test prompt

**Independent Test**: Clone repo → set FOUNDRY_PROJECT_CONNECTION_STRING → run `python scripts/deploy_agent.py --agent <agent-1>` → send a prompt → verify response

### Implementation for User Story 1

- [X] T010 [P] [US1] Create first agent config subclass extending FoundryBaseConfig with agent_name, agent_model, agent_instructions_path defaults in agents/<agent-1>/config.py
- [X] T011 [P] [US1] Write first agent system instructions as versioned markdown in agents/<agent-1>/instructions.md
- [X] T012 [P] [US1] Implement sample function tool (e.g., greeting or echo) using FunctionTool pattern in agents/<agent-1>/tools/sample_tool.py
- [X] T013 [P] [US1] Create knowledge source integration stub returning None when KNOWLEDGE_SOURCE_ENABLED is false with get_knowledge_tool(config) signature in agents/<agent-1>/integrations/knowledge.py
- [X] T014 [P] [US1] Create GitHub OpenAPI integration stub returning None when GITHUB_OPENAPI_ENABLED is false with get_github_openapi_tool(config) signature in agents/<agent-1>/integrations/github_openapi.py
- [X] T015 [US1] Register first agent as AgentRegistryEntry in REGISTRY within agents/registry.py
- [X] T016 [US1] Implement deploy CLI script with argparse (--agent <name>, --all, mutually exclusive), registry resolution, per-agent error isolation, and summary output per deploy-script contract in scripts/deploy_agent.py
- [X] T017 [US1] Implement run lifecycle helper with create_thread, send_message, create_and_process_run, retrieve_response, and failure/cancellation handling with configurable timeout (default 120s) in agents/_base/run.py

**Checkpoint**: At this point, a developer can deploy one agent and interact with it via the run helper. User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Add and Deploy a New Agent Independently (Priority: P2)

**Goal**: Prove the multi-agent extensibility pattern — add a second agent without modifying any existing agent or shared code

**Independent Test**: Create new agent folder → register it → run `deploy_agent.py --agent <agent-2>` → verify it responds independently. Run `deploy_agent.py --all` → verify both deploy and one failing doesn't block the other.

### Implementation for User Story 2

- [X] T018 [P] [US2] Create second agent config subclass with distinct agent_name and model defaults in agents/<agent-2>/config.py
- [X] T019 [P] [US2] Write second agent system instructions in agents/<agent-2>/instructions.md
- [X] T020 [P] [US2] Implement sample function tool with a different capability than agent-1 in agents/<agent-2>/tools/sample_tool.py
- [X] T021 [P] [US2] Create knowledge source and GitHub OpenAPI integration stubs in agents/<agent-2>/integrations/knowledge.py and agents/<agent-2>/integrations/github_openapi.py
- [X] T022 [US2] Register second agent as AgentRegistryEntry in REGISTRY within agents/registry.py (single line addition, zero changes to agent-1)

**Checkpoint**: At this point, two agents are independently deployable. `deploy_agent.py --all` deploys both. Adding agent required exactly two locations: the agent folder and one registry line (SC-002).

---

## Phase 5: User Story 3 — Automated CI/CD Deployment Across Environments (Priority: P3)

**Goal**: Automated dev deployment on push to main, manual qa/prod promotion with OIDC auth and infra provisioning

**Independent Test**: Push a change to main → observe test pipeline passes and deploy pipeline provisions infra + deploys agents to dev. Manual dispatch to qa/prod can be verified separately.

### Implementation for User Story 3

- [X] T023 [P] [US3] Create test pipeline with lint (Black --check, isort --check, flake8) and unit test (pytest -m "not integration") stages triggered on PR and push to main in .github/workflows/test.yml
- [X] T024 [US3] Create deploy pipeline with workflow_dispatch inputs (environment, infra_tool, use_existing_foundry, agent_target), OIDC auth via azure/login@v2, 6-stage pipeline (validate → provision shared infra → provision foundry → export outputs → deploy agents → integration tests), per-environment secrets, auto-deploy dev on push to main, prod approval gate per cicd-pipeline contract in .github/workflows/deploy.yml

**Checkpoint**: At this point, CI/CD is fully automated. Dev deploys on push, qa/prod via manual dispatch. OIDC auth, no client secrets (SC-007).

---

## Phase 6: User Story 4 — Onboard via Jupyter Notebooks (Priority: P4)

**Goal**: Python developers new to Foundry can learn interactively via two notebooks

**Independent Test**: Open each notebook in Jupyter → run all cells top-to-bottom → verify expected output without errors

### Implementation for User Story 4

- [X] T025 [P] [US4] Create setup-and-connect notebook with configurable AGENT_NAME variable, Mode A (existing Foundry) and Mode B (new Foundry) sections, AIProjectClient initialisation, and connection verification in notebooks/01_setup_and_connect.ipynb
- [X] T026 [P] [US4] Create build-and-run-agent notebook with agent creation, thread creation, message posting, run execution, response display, and function tool demonstration — agent-agnostic via top-level AGENT_NAME variable — in notebooks/02_build_and_run_agent.ipynb

**Checkpoint**: At this point, onboarding notebooks are complete. A new developer can connect to Foundry and build an agent interactively (SC-006).

---

## Phase 7: User Story 5 — Provision New Foundry Infrastructure from Scratch (Priority: P5)

**Goal**: Greenfield provisioning of all Azure infrastructure via Terraform or Bicep, including optional Foundry resource creation

**Independent Test**: Run `terraform apply` or `az deployment` with `use_existing_foundry=false` → verify Foundry resource, project, Key Vault exist in Azure → deploy an agent to the new project

### Terraform Implementation

- [X] T027 [P] [US5] Create Terraform provider configuration (azurerm >= 4.0, required_version >= 1.5) with remote state backend (Azure Blob Storage) in infra/terraform/providers.tf
- [X] T028 [P] [US5] Create Terraform variable definitions (prefix, environment, use_existing_foundry, enable_knowledge_source, ci_principal_id, existing_foundry_connection_string) in infra/terraform/variables.tf
- [X] T029 [US5] Create Terraform main with resource group, Key Vault (always), conditional Foundry resource (azurerm_cognitive_account kind=AIServices with custom_subdomain_name), conditional AI Search, and RBAC role assignments (Contributor on RG, Cognitive Services User on Foundry, Key Vault Secrets User on KV) using {prefix}-{resource}-{env} naming in infra/terraform/main.tf
- [X] T030 [P] [US5] Create Terraform outputs (project_connection_string, resource_group_name, key_vault_name) in infra/terraform/outputs.tf
- [X] T031 [P] [US5] Create environment-specific tfvars with appropriate prefix values in infra/terraform/envs/dev.tfvars, infra/terraform/envs/qa.tfvars, and infra/terraform/envs/prod.tfvars

### Bicep Implementation

- [X] T032 [P] [US5] Create Bicep foundry-resource module (Microsoft.CognitiveServices/accounts@2024-10-01, kind AIServices, SystemAssigned identity, custom subdomain) in infra/bicep/modules/foundry-resource.bicep
- [X] T033 [P] [US5] Create Bicep foundry-project module for project within the Foundry resource in infra/bicep/modules/foundry-project.bicep
- [X] T034 [P] [US5] Create Bicep keyvault module (Microsoft.KeyVault/vaults@2023-07-01, RBAC authorization enabled) in infra/bicep/modules/keyvault.bicep
- [X] T035 [P] [US5] Create Bicep AI Search module (Microsoft.Search/searchServices, conditional on enableKnowledgeSource) in infra/bicep/modules/ai-search.bicep
- [X] T036 [US5] Create Bicep main orchestrator composing all modules with conditional Foundry provisioning, {prefix}-{resource}-{env} naming, RBAC role assignments, and outputs (projectConnectionString, resourceGroupName, keyVaultName) in infra/bicep/main.bicep
- [X] T037 [P] [US5] Create environment-specific bicepparam files with appropriate prefix values in infra/bicep/parameters/dev.bicepparam, infra/bicep/parameters/qa.bicepparam, and infra/bicep/parameters/prod.bicepparam

**Checkpoint**: At this point, both Terraform and Bicep produce identical Azure environments (SC-005). Switching between use-existing and create-new requires a single boolean (SC-008).

---

## Phase 8: User Story 6 — Run Tests Locally and in CI (Priority: P6)

**Goal**: Unit tests pass without credentials, integration tests pass against live Foundry with test-prefixed agent names and full teardown

**Independent Test**: Run `pytest -m "not integration"` locally (no creds) → all pass. Run `pytest -m integration` with FOUNDRY_PROJECT_CONNECTION_STRING → tests create temp agents, assert, teardown.

### Implementation for User Story 6

- [X] T038 [P] [US6] Create root conftest with shared fixtures (mock_config, mock_client, mock_agents_client) and pytest markers registration (integration, agent_1, agent_2) in tests/conftest.py
- [X] T039 [P] [US6] Create unit tests for FoundryBaseConfig (env var loading, defaults, validation) with mocked env vars in tests/_base/test_config.py
- [X] T040 [P] [US6] Create unit tests for AIProjectClient singleton init (credential handling, connection string) with mocked SDK in tests/_base/test_client.py
- [X] T041 [P] [US6] Create unit tests for create_or_update_agent (create path, update path, missing instructions, empty instructions, conditional tool appending, edge cases: invalid connection string error, empty registry warning, concurrent deploy idempotency) with mocked agents_client in tests/_base/test_agent_factory.py
- [X] T042 [P] [US6] Create agent-1 conftest with agent-specific fixtures and @pytest.mark.agent_1 marker in tests/<agent-1>/conftest.py
- [X] T043 [P] [US6] Create unit tests for agent-1 tools (function input/output, edge cases) in tests/<agent-1>/test_tools.py
- [X] T044 [US6] Create integration tests for agent create/update against live Foundry with test-{agent}-{timestamp} naming, idempotency verification, and full teardown — auto-skip when FOUNDRY_PROJECT_CONNECTION_STRING unset — must also verify edge cases: failed/cancelled run detection, KV-unreachable error surfacing — in tests/<agent-1>/test_agent_create.py
- [X] T045 [US6] Create integration tests for full run lifecycle (create thread, post message, run agent, assert response, cleanup) with @pytest.mark.integration in tests/<agent-1>/test_agent_run.py

### Agent-2 Tests

- [X] T045a [P] [US6] Create agent-2 conftest with agent-specific fixtures and @pytest.mark.agent_2 marker in tests/<agent-2>/conftest.py
- [X] T045b [P] [US6] Create unit tests for agent-2 tools (function input/output, edge cases) in tests/<agent-2>/test_tools.py

**Checkpoint**: At this point, full test coverage is in place. Unit tests run without credentials, integration tests verify live behaviour with cleanup (SC-003, SC-009).

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final validation, and cross-story quality improvements

- [X] T046 [P] Create README.md with shields.io badges (license, Python version, Azure, Terraform, Bicep, GitHub Actions, repo stats), project overview, architecture diagram, decision guide (Terraform vs Bicep, existing vs new Foundry), setup instructions, and links to notebooks and spec at project root
- [X] T047 [P] Verify and update .env.example to reflect all environment variables added across all user stories at project root
- [X] T048 Run quickstart.md validation end-to-end: clone → configure → deploy → test → add agent → verify all steps succeed. Also verify SC-001 (first agent deployed and responding within 15 minutes of clone).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories
- **User Stories (Phases 3–8)**: All depend on Foundational phase completion
  - US1 (Phase 3) → must complete first as MVP baseline
  - US2 (Phase 4) → depends on US1 (extends the pattern US1 establishes)
  - US3 (Phase 5) → depends on US1 (pipeline deploys agents created via US1 patterns)
  - US4 (Phase 6) → depends on US1 (notebooks interact with agents from US1)
  - US5 (Phase 7) → can start after Foundational (infra is independent of agent code)
  - US6 (Phase 8) → depends on US1 (tests need agent code to test against)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — no dependencies on other stories
- **US2 (P2)**: After US1 — extends the agent pattern
- **US3 (P3)**: After US1 — can be parallel with US2, US4, US5 if US1 is done
- **US4 (P4)**: After US1 — can be parallel with US2, US3, US5 if US1 is done
- **US5 (P5)**: After Foundational — infrastructure provisioning is independent and can be parallel with US1; however, the independent _test_ (deploying an agent onto the new infra) requires US1's deploy script
- **US6 (P6)**: After US1 — tests need agent implementations to test

### Within Each User Story

- Models/configs before services
- Services/factories before scripts/pipelines
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks T002–T004 marked [P] can run in parallel (after T001)
- Foundational: T005, T006, T009 can run in parallel; then T007; then T008
- US1: T010–T014 can all run in parallel; T015 depends on T010; T016 depends on T007+T008; T017 depends on T006
- US2: T018–T021 can all run in parallel; T022 depends on T018
- US3: T023 can run in parallel with T024 start, but T024 is the main work
- US4: T025 and T026 can run in parallel
- US5: All Terraform module tasks (T027, T028, T030, T031) parallel; T029 depends on T028. All Bicep module tasks (T032–T035, T037) parallel; T036 depends on T032–T035. Terraform and Bicep tracks are fully independent.
- US6: T038–T043 can all run in parallel; T044–T045 depend on T038+T041

---

## Parallel Example: User Story 1

```bash
# Launch all agent folder files in parallel (different files, no deps):
T010: "Create first agent config in agents/<agent-1>/config.py"
T011: "Write first agent instructions in agents/<agent-1>/instructions.md"
T012: "Implement sample function tool in agents/<agent-1>/tools/sample_tool.py"
T013: "Create knowledge stub in agents/<agent-1>/integrations/knowledge.py"
T014: "Create GitHub OpenAPI stub in agents/<agent-1>/integrations/github_openapi.py"

# Then sequentially:
T015: "Register first agent in agents/registry.py" (needs T010 config class)
T016: "Implement deploy script in scripts/deploy_agent.py" (needs registry + factory)
T017: "Implement run lifecycle helper in agents/_base/run.py" (needs client)
```

## Parallel Example: User Story 5 (Infrastructure)

```bash
# Terraform track (all modules parallel, then main):
T027: "Terraform providers.tf"  |  T028: "Terraform variables.tf"  |  T030: "Terraform outputs.tf"  |  T031: "Terraform envs/*.tfvars"
T029: "Terraform main.tf" (after T028)

# Bicep track (all modules parallel, then main):
T032: "foundry-resource.bicep"  |  T033: "foundry-project.bicep"  |  T034: "keyvault.bicep"  |  T035: "ai-search.bicep"  |  T037: "parameters/*.bicepparam"
T036: "Bicep main.bicep" (after T032–T035)

# Both tracks can run fully in parallel with each other
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Deploy one agent, send a prompt, verify response
5. Deploy/demo if ready — this is the minimum viable product

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. **US1** → Deploy first agent, verify response → **MVP!**
3. **US2** → Add second agent, verify independent deploy
4. **US3** → Automated CI/CD pipeline, verify dev auto-deploy
5. **US4** → Notebooks, verify top-to-bottom execution
6. **US5** → Infrastructure provisioning, verify greenfield deploy
7. **US6** → Full test coverage, verify unit + integration pass
8. Polish → README, validation

### Parallel Team Strategy

With multiple developers after Foundational is complete:

- Developer A: US1 (MVP) → US2 (extends the pattern)
- Developer B: US5 (infrastructure — independent of agent code)
- Developer C: US3 (CI/CD — can start with placeholder agents)
- After US1 done: US4, US6 can begin

---

## FR Coverage Matrix

| FR | Task(s) | Phase |
|----|---------|-------|
| FR-001 | T007 | Foundational |
| FR-002 | T008 | Foundational |
| FR-003 | T010–T014, T018–T021 | US1, US2 |
| FR-004 | T005 | Foundational |
| FR-005 | T011, T019 | US1, US2 |
| FR-006 | T006 | Foundational |
| FR-007 | T017 | US1 |
| FR-008 | T013, T021 | US1, US2 |
| FR-009 | T014, T021 | US1, US2 |
| FR-010 | T008 | Foundational |
| FR-011 | T029, T036 | US5 |
| FR-012 | T029, T032 | US5 |
| FR-013 | T029, T035 | US5 |
| FR-014 | T029, T036, T031, T037 | US5 |
| FR-015 | T030, T036 | US5 |
| FR-016 | T027 | US5 |
| FR-016a | T029, T036 | US5 |
| FR-017 | T023 | US3 |
| FR-018 | T024 | US3 |
| FR-019 | T024 | US3 |
| FR-020 | T024 | US3 |
| FR-021 | T024 | US3 |
| FR-022 | T039–T043, T045a–T045b | US6 |
| FR-023 | T044–T045 | US6 |
| FR-024 | T042–T043, T045a | US6 |
| FR-025 | T044 | US6 |
| FR-026 | T025 | US4 |
| FR-027 | T026 | US4 |
| FR-028 | T025, T026 | US4 |
| FR-029 | T016 | US1 |
| FR-030 | T016 | US1 |

---

## Notes

- [P] tasks operate on different files with no dependencies — safe to execute in parallel
- [Story] labels map tasks to specific user stories for traceability
- Each user story is independently completable and testable after Foundational phase
- `<agent-1>` and `<agent-2>` are placeholder names — choose descriptive names during implementation
- Commit after each task or logical group of parallel tasks
- Stop at any checkpoint to validate the story independently
- All contracts (registry, factory, deploy-script, cicd-pipeline) are in specs/003-foundry-agent-platform/contracts/
- Research findings (SDK patterns, Terraform/Bicep resources, OIDC setup, pydantic-settings) are in specs/003-foundry-agent-platform/research.md
