# Tasks: Migrate to New Foundry SDK (azure-ai-projects v2)

**Input**: Design documents from `/specs/005-migrate-to-new-foundry/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story. Each story is independently testable after its phase completes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US4) this task belongs to
- Exact file paths included in every task description

---

## Phase 1: Setup

**Purpose**: Update dependencies and environment configuration before any code changes

- [x] T001 Update dependency versions in pyproject.toml — replace `azure-ai-agents` with `azure-ai-projects>=2.0.0`, remove `azure-ai-agents` entry
- [x] T002 [P] Update dependency versions in requirements.txt — replace `azure-ai-agents` with `azure-ai-projects>=2.0.0`
- [x] T003 [P] Rename env var in .env.example from `FOUNDRY_PROJECT_CONNECTION_STRING` to `AZURE_AI_PROJECT_ENDPOINT`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on — client singleton, base config, and tool helper

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Migrate client singleton in agents/_base/client.py — replace `AgentsClient` import/type with `AIProjectClient` from `azure.ai.projects`, rename `get_agents_client()` to `get_project_client()`, accept `endpoint` parameter instead of connection string, keep singleton + `reset_client()` pattern per contracts/client.md
- [x] T005 Migrate base config in agents/_base/config.py — rename field `foundry_project_connection_string` to `azure_ai_project_endpoint`, update env var source to `AZURE_AI_PROJECT_ENDPOINT`, keep all other fields unchanged per data-model.md Section 1.1
- [x] T006 Rewrite tool creation helper in agents/_base/tools/__init__.py — implement `create_function_tool(func, description=None) -> FunctionTool` that inspects function signature + docstring to build JSON schema, returns `FunctionTool(name=..., parameters=schema, description=..., strict=True)` per contracts/tools.md

**Checkpoint**: Foundation ready — client, config, and tool infrastructure use new SDK

---

## Phase 3: User Story 1 — Deploy Agent with New SDK (Priority: P1) 🎯 MVP

**Goal**: Developer can deploy/update agents using `create_version` + `PromptAgentDefinition`

**Independent Test**: Run `python scripts/deploy_agent.py --name code-helper` — agent is created/versioned in Foundry

### Implementation for User Story 1

- [x] T007 [US1] Migrate agent factory in agents/_base/agent_factory.py — replace `create_agent()`/`update_agent()` with `project_client.agents.create_version(agent_name=..., definition=PromptAgentDefinition(...))`, remove list-and-match logic (create_version is inherently idempotent), collect tools as objects (not flattened definitions) per contracts/agent-factory.md
- [x] T008 [P] [US1] Migrate code_helper config in agents/code_helper/config.py — rename `foundry_project_connection_string` references to `azure_ai_project_endpoint`, update any env var references
- [x] T009 [P] [US1] Migrate doc_assistant config in agents/doc_assistant/config.py — rename `foundry_project_connection_string` references to `azure_ai_project_endpoint`, update any env var references
- [x] T010 [P] [US1] Update code_helper tool definitions in agents/code_helper/tools/sample_tool.py and agents/code_helper/tools/__init__.py — use `create_function_tool()` with new helper, verify TOOLS list exports correctly
- [x] T011 [P] [US1] Update doc_assistant tool definitions in agents/doc_assistant/tools/sample_tool.py and agents/doc_assistant/tools/__init__.py — use `create_function_tool()` with new helper, verify TOOLS list exports correctly
- [x] T012 [US1] Update registry usage in agents/registry.py — ensure factory function references use `get_project_client()` and new config field names if referenced directly
- [x] T013 [US1] Update deploy script in scripts/deploy_agent.py — adjust any direct SDK references to use new client/factory patterns

**Checkpoint**: Agents can be deployed/updated via the new `create_version` API

---

## Phase 4: User Story 2 — Run Agent Conversation (Priority: P1)

**Goal**: Developer can send messages and receive responses using OpenAI conversations/responses model

**Independent Test**: Run notebook 02 end-to-end — conversation created, response received, conversation cleaned up

### Implementation for User Story 2

- [x] T014 [US2] Rewrite run lifecycle in agents/_base/run.py — replace threads/messages/runs with `openai_client.conversations.create()`, `openai_client.responses.create(conversation=..., extra_body={"agent_reference": {...}})`, implement function call handling loop (check `function_call` output items, execute, submit `function_call_output`), extract text via `response.output_text`, cleanup conversation per contracts/run.md
- [x] T015 [US2] Migrate notebook 01 in notebooks/01_setup_and_connect.ipynb — replace `AgentsClient` with `AIProjectClient`, update import from `azure.ai.projects`, change env var to `AZURE_AI_PROJECT_ENDPOINT`, update connection verification cell
- [x] T016 [US2] Migrate notebook 02 in notebooks/02_build_and_run_agent.ipynb — replace install cell deps, replace `AgentsClient` connection cell with `AIProjectClient`, update agent deploy cell to use new factory/config field names, rewrite conversation cell to use `openai_client.conversations`/`responses` pattern, update cleanup cell to delete conversation, remove `RunStatus`/`MessageRole` imports
- [x] T017 [US2] Migrate notebook 03 in notebooks/03_scaffold_agent.ipynb — update SDK references and example code to use new patterns

**Checkpoint**: Full agent conversation lifecycle works end-to-end with new SDK

---

## Phase 5: User Story 4 — Unit Tests Pass Without Azure Credentials (Priority: P1)

**Goal**: All unit tests pass with mocked new SDK classes, no Azure credentials required

**Independent Test**: Run `pytest tests/ -m "not integration" -v` — all tests green

### Implementation for User Story 4

- [x] T018 [US4] Update root test fixtures in tests/conftest.py — mock `AIProjectClient` instead of `AgentsClient`, add OpenAI client mock fixture with `.conversations` and `.responses` sub-mocks per research.md Decision 8
- [x] T019 [P] [US4] Migrate tests/_base/test_client.py — test `get_project_client()` singleton with `AIProjectClient`, test `reset_client()`, test endpoint mismatch `ValueError`
- [x] T020 [P] [US4] Migrate tests/_base/test_config.py — test `azure_ai_project_endpoint` field loads from `AZURE_AI_PROJECT_ENDPOINT` env var
- [x] T021 [P] [US4] Migrate tests/_base/test_agent_factory.py — mock `project_client.agents.create_version()`, verify `PromptAgentDefinition` is constructed with correct model/instructions/tools, remove old create/update/list agent mocks
- [x] T022 [P] [US4] Migrate tests/_base/test_run.py — mock OpenAI client's `conversations.create()`, `responses.create()`, `conversations.delete()`, test function call handling loop, test `AgentRunError` on failure, verify `response.output_text` extraction
- [x] T023 [US4] Update tests/code_helper/conftest.py — update config fixtures to use `azure_ai_project_endpoint` field name, update client mocks to `AIProjectClient`
- [x] T024 [P] [US4] Migrate tests/code_helper/test_tools.py — verify `create_function_tool()` returns `FunctionTool` with correct JSON schema for `greet_user` function
- [x] T025 [P] [US4] Migrate tests/code_helper/test_agent_create.py — update integration test to use `create_version` pattern (or keep as integration-only, verify mocks)
- [x] T026 [P] [US4] Migrate tests/code_helper/test_agent_run.py — update integration test to use conversations/responses pattern
- [x] T027 [US4] Update tests/doc_assistant/conftest.py — update config fixtures to use `azure_ai_project_endpoint` field name, update client mocks
- [x] T028 [P] [US4] Migrate tests/doc_assistant/test_tools.py — verify `create_function_tool()` returns correct JSON schema for doc_assistant tool
- [x] T029 [P] [US4] Migrate tests/doc_assistant/test_agent_create.py — update integration test to use `create_version` pattern
- [x] T030 [P] [US4] Migrate tests/doc_assistant/test_agent_run.py — update integration test to use conversations/responses pattern
- [x] T031 [US4] Run full unit test suite: `pytest tests/ -m "not integration" -v` — verify all tests pass without Azure credentials

**Checkpoint**: All unit tests pass, mocking the new SDK surface correctly

---

## Phase 6: User Story 3 — Scaffold New Agent (Priority: P2)

**Goal**: `create_agent.py` generates boilerplate using new SDK patterns

**Independent Test**: Run `python scripts/create_agent.py --name test-agent` — generated files use `AIProjectClient`, `create_version`, `PromptAgentDefinition`, `azure_ai_project_endpoint`, and JSON schema `FunctionTool`

### Implementation for User Story 3

- [x] T032 [US3] Update scaffolding script templates in scripts/create_agent.py — update generated config template to use `azure_ai_project_endpoint`, update generated tool template to use JSON schema `FunctionTool`, update generated integration test template to use conversations/responses pattern per research.md Decision 10
- [x] T033 [US3] Migrate tests/scaffolding/test_create_agent.py — update assertions for new config field name (`azure_ai_project_endpoint`), new tool schema format (`FunctionTool(name=..., parameters=..., description=...)`), and new integration test template (conversations/responses pattern)

**Checkpoint**: New agents are scaffolded with correct new SDK patterns and scaffolding tests pass

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, README, and final validation across all stories

- [x] T034 [P] Update docs/custom-tools-guide.md — replace `FunctionTool(functions=[callable])` examples with JSON schema `FunctionTool(name=..., parameters=..., description=...)` pattern, update imports from `azure.ai.projects.models`
- [x] T035 [P] Update docs/infrastructure-guide.md — replace `FOUNDRY_PROJECT_CONNECTION_STRING` references with `AZURE_AI_PROJECT_ENDPOINT`, update any SDK version references
- [x] T036 [P] Update docs/scaffolding-guide.md — update SDK references, config field names, and example code to use new patterns
- [x] T037 [P] Update README.md — update SDK version badges, replace `azure-ai-agents` references with `azure-ai-projects v2`, update quickstart code examples, update env var references
- [x] T038 Run quickstart.md validation — execute the 6 steps from specs/005-migrate-to-new-foundry/quickstart.md to verify migration works end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US-1 Deploy (Phase 3)**: Depends on Phase 2 (client + config + tool helper)
- **US-2 Run (Phase 4)**: Depends on Phase 2 (client) + Phase 3 (agent factory for notebooks)
- **US-4 Tests (Phase 5)**: Depends on Phase 3 (factory code to mock) + Phase 4 (run code to mock)
- **US-3 Scaffold (Phase 6)**: Depends on Phase 2 (patterns to template)
- **Polish (Phase 7)**: Depends on all prior phases

### User Story Dependencies

- **US-1 (P1)**: Requires Foundational only — can start after Phase 2
- **US-2 (P1)**: Requires US-1 (notebooks need deployed agent) — starts after Phase 3
- **US-4 (P1)**: Requires US-1 + US-2 (tests mirror implementations) — starts after Phase 4
- **US-3 (P2)**: Requires Foundational only (templates copy patterns) — can start after Phase 2, but logically after US-1 patterns are finalized

### Within Each User Story

- Config changes before implementation code
- Core module before dependent modules
- Implementation before tests (tests validate implementations)
- All [P] tasks within a phase can run in parallel

### Parallel Opportunities

- T002 + T003 can run in parallel (Phase 1 — different files)
- T008 + T009 can run in parallel (Phase 3 — code_helper/doc_assistant configs)
- T010 + T011 can run in parallel (Phase 3 — code_helper/doc_assistant tools)
- T019 + T020 + T021 + T022 can run in parallel (Phase 5 — different _base test files)
- T024 + T025 + T026 can run in parallel (Phase 5 — code_helper tests)
- T028 + T029 + T030 can run in parallel (Phase 5 — doc_assistant tests)
- T034 + T035 + T036 + T037 can run in parallel (Phase 7 — different doc files)

---

## Parallel Example: User Story 1

```text
# After T007 (factory) completes, launch all parallel agent-specific tasks:
T008: Migrate code_helper config in agents/code_helper/config.py
T009: Migrate doc_assistant config in agents/doc_assistant/config.py
T010: Update code_helper tool definitions in agents/code_helper/tools/
T011: Update doc_assistant tool definitions in agents/doc_assistant/tools/
```

## Parallel Example: User Story 4 (Tests)

```text
# After T018 (conftest) completes, launch all parallel _base test migrations:
T019: Migrate tests/_base/test_client.py
T020: Migrate tests/_base/test_config.py
T021: Migrate tests/_base/test_agent_factory.py
T022: Migrate tests/_base/test_run.py

# After T023 (code_helper conftest), launch code_helper tests:
T024: Migrate tests/code_helper/test_tools.py
T025: Migrate tests/code_helper/test_agent_create.py
T026: Migrate tests/code_helper/test_agent_run.py
```

---

## Implementation Strategy

### MVP First (US-1 + US-2)

1. Complete Phase 1: Setup — update deps and env var
2. Complete Phase 2: Foundational — client, config, tool helper
3. Complete Phase 3: US-1 — agent deployment works with new SDK
4. Complete Phase 4: US-2 — conversation lifecycle works
5. **STOP and VALIDATE**: Deploy an agent and run a conversation manually

### Incremental Delivery

1. Setup + Foundational → New SDK installed, core infra migrated
2. US-1 → Agents deploy with `create_version` → Manual validation
3. US-2 → Conversations work → Notebook validation (MVP!)
4. US-4 → All unit tests green → CI confidence
5. US-3 → Scaffolding uses new patterns → Template validation
6. Polish → Docs updated → Repo fully migrated

### Key Risk: Breaking Change

This is a breaking migration — the old SDK is completely replaced. There is no incremental path. Once Phase 2 lands, all code must use the new SDK. Plan for a single dedicated migration effort rather than piecemeal changes.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [US*] label maps task to specific user story for traceability
- All tasks include exact file paths for unambiguous implementation
- `create_version()` is idempotent — simplifies factory significantly vs old create/update/list pattern
- The `openai_client` from `get_openai_client()` is a context manager — must use `with` statement
- Function call handling is now manual (loop on output items) vs old `enable_auto_function_calls`
- Commit after each phase checkpoint for safe rollback points
