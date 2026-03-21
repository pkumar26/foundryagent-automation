# Tasks: Agent Scaffolding Automation

**Input**: Design documents from `/specs/004-agent-scaffolding/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included — the spec requires tests for the scaffolding script itself (FR-7, FR-9), and the script generates test stubs for each scaffolded agent.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Scripts**: `scripts/` at repository root
- **Tests**: `tests/scaffolding/` for scaffolding script tests
- **Docs**: `docs/` at repository root, `README.md` at repository root
- **Workflows**: `.github/workflows/`

---

## Phase 1: Setup

**Purpose**: Create the scaffolding script skeleton, test directory, and utility functions

- [X] T001 Create scaffolding script entry point with CLI argument parsing in `scripts/create_agent.py`
- [X] T002 [P] Create test directory with `tests/scaffolding/__init__.py` and `tests/scaffolding/test_create_agent.py` (empty test file with imports)
- [X] T003 [P] Add `scaffolding` pytest marker to `pyproject.toml` under `[tool.pytest.ini_options]` markers list

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core validation and name-derivation utilities that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement agent name validation function in `scripts/create_agent.py` — validate kebab-case regex `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, max 50 chars, reject Python reserved words via `keyword.iskeyword`
- [X] T005 [P] Implement name derivation helpers in `scripts/create_agent.py` — `to_module_name()` (kebab→snake), `to_class_prefix()` (kebab→PascalCase), `to_config_class_name()` (PascalCase + "Config")
- [X] T006 [P] Implement existence checks in `scripts/create_agent.py` — verify agent dir, test dir, and registry entry do not already exist; return clear error messages per contract
- [X] T007 Implement file-writing utility in `scripts/create_agent.py` — `_write_file(path, content)` that creates parent dirs and writes content with UTF-8 encoding

**Checkpoint**: Foundation ready — all validation and utility functions are in place

---

## Phase 3: User Story 1 — Scaffold a New Agent via CLI (Priority: P1) MVP

**Goal**: `python scripts/create_agent.py --name my-agent` generates all agent files, test stubs, and registry entry

**Independent Test**: Run `python scripts/create_agent.py --name test-agent`, verify 13 files created under `agents/test_agent/` and `tests/test_agent/`, verify registry.py updated, run `pytest tests/test_agent/ -v`

### Tests for User Story 1

- [X] T008 [P] [US1] Write test `test_validate_name_valid` and `test_validate_name_invalid` in `tests/scaffolding/test_create_agent.py` — valid kebab-case passes, invalid formats rejected
- [X] T009 [P] [US1] Write test `test_name_derivation` in `tests/scaffolding/test_create_agent.py` — verify `to_module_name`, `to_class_prefix`, `to_config_class_name` outputs
- [X] T010 [P] [US1] Write test `test_scaffold_creates_agent_directory` in `tests/scaffolding/test_create_agent.py` — verify all 8 agent files created with correct content (uses `tmp_path`)
- [X] T011 [P] [US1] Write test `test_scaffold_creates_test_directory` in `tests/scaffolding/test_create_agent.py` — verify all 5 test files created with correct content (uses `tmp_path`)
- [X] T012 [P] [US1] Write test `test_scaffold_updates_registry` in `tests/scaffolding/test_create_agent.py` — verify import line and AgentRegistryEntry appended to a mock registry file
- [X] T013 [P] [US1] Write test `test_scaffold_rejects_existing_agent` in `tests/scaffolding/test_create_agent.py` — verify script fails with error when agent dir already exists

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement agent file templates in `scripts/create_agent.py` — `_template_config()`, `_template_instructions()`, `_template_sample_tool()`, `_template_tools_init()`, `_template_github_openapi()`, `_template_knowledge()` using `textwrap.dedent` and f-strings; match patterns from `agents/code_helper/` exactly
- [X] T015 [P] [US1] Implement test file templates in `scripts/create_agent.py` — `_template_conftest()`, `_template_test_tools()`, `_template_test_agent_create()`, `_template_test_agent_run()` matching patterns from `tests/code_helper/`
- [X] T016 [US1] Implement `_generate_agent_files()` in `scripts/create_agent.py` — create `agents/{module}/` directory tree and write all 8 files using templates from T014
- [X] T017 [US1] Implement `_generate_test_files()` in `scripts/create_agent.py` — create `tests/{module}/` directory tree and write all 5 files using templates from T015
- [X] T018 [US1] Implement `_update_registry()` in `scripts/create_agent.py` — read `agents/registry.py`, insert import after last config import, insert `AgentRegistryEntry` before closing `])`, write file back
- [X] T019 [US1] Implement `main()` orchestration in `scripts/create_agent.py` — wire together: parse args → validate → check existence → generate agent files → generate test files → update registry → print summary
- [X] T020 [US1] Run all scaffolding tests: `pytest tests/scaffolding/ -v` and verify all pass; include a timing assertion (< 2s) in `test_scaffold_creates_agent_directory` to validate NFR-4
- [X] T021 [US1] Run linting on generated script: `black --check scripts/create_agent.py && isort --check scripts/create_agent.py && flake8 scripts/create_agent.py`

**Checkpoint**: CLI scaffolding with `--name` fully works. Can scaffold an agent, run its tests, and deploy it.

---

## Phase 4: User Story 2 — Scaffold Agent from YAML Input File (Priority: P2)

**Goal**: `python scripts/create_agent.py --from-file agent-config.yaml` reads agent definition from YAML and scaffolds identically to CLI mode

**Independent Test**: Create a test YAML file, run with `--from-file`, verify same output as `--name`

### Tests for User Story 2

- [X] T022 [P] [US2] Write test `test_parse_yaml_valid` in `tests/scaffolding/test_create_agent.py` — valid YAML with name+model parsed correctly
- [X] T023 [P] [US2] Write test `test_parse_yaml_missing_name` in `tests/scaffolding/test_create_agent.py` — missing name field raises validation error
- [X] T024 [P] [US2] Write test `test_parse_yaml_file_not_found` in `tests/scaffolding/test_create_agent.py` — non-existent file path raises error
- [X] T025 [P] [US2] Write test `test_scaffold_from_yaml` in `tests/scaffolding/test_create_agent.py` — end-to-end: YAML file → same files generated as CLI mode
- [X] T025b [P] [US2] Write test `test_from_file_ignores_cli_model` in `tests/scaffolding/test_create_agent.py` — verify that when `--from-file` is used, any `--model` CLI flag is silently ignored and the model from the YAML file takes precedence

### Implementation for User Story 2

- [X] T026 [US2] Implement `_parse_yaml_file()` in `scripts/create_agent.py` — simple key-value parser for flat YAML subset (`name: value` lines), no PyYAML dependency; validate required `name` field present
- [X] T027 [US2] Update `main()` in `scripts/create_agent.py` — when `--from-file` is provided, call `_parse_yaml_file()` to extract name and model, then proceed through same scaffold pipeline
- [X] T028 [US2] Run all scaffolding tests including new YAML tests: `pytest tests/scaffolding/ -v`

**Checkpoint**: Both CLI `--name` and `--from-file` modes work. YAML input produces identical output.

---

## Phase 5: User Story 4 — Updated README and Dedicated Scaffolding Guide (Priority: P2)

**Goal**: README documents all agent creation methods; dedicated guide provides setup, usage, YAML format, FAQ, and troubleshooting

**Independent Test**: Read README and `docs/scaffolding-guide.md`; verify all sections present, links work, error table matches script's actual error messages

### Implementation for User Story 4

- [X] T029 [US4] Update README.md "Adding a New Agent" section — replace 3-step manual instructions with multi-method overview (automated CLI/YAML + manual) per documentation contract; link to `docs/scaffolding-guide.md`
- [X] T030 [US4] Update README.md "Architecture" section — add `scripts/create_agent.py` and `docs/` directory to the architecture tree diagram
- [X] T031 [US4] Update README.md "CI/CD" table — add `create-agent.yml` row: `| create-agent.yml | Manual dispatch | Scaffold new agent + open PR |`
- [X] T032 [US4] Create `docs/scaffolding-guide.md` with all 10 sections per documentation contract: Overview, Prerequisites, Quick Start, CLI Reference, YAML Input Reference, GitHub Actions, What Gets Generated, Customise Your Agent, FAQ (≥6 entries), Troubleshooting (≥5 error→resolution entries); include shields.io badges
- [X] T032b [US4] Create `notebooks/03_scaffold_agent.ipynb` — walkthrough notebook demonstrating: (1) CLI scaffolding with `--name`, (2) verifying generated files, (3) running generated tests, (4) deploying the scaffolded agent; follows existing notebook patterns from `notebooks/01_setup_and_connect.ipynb`

**Checkpoint**: All documentation is complete and consistent with the CLI implementation.

---

## Phase 6: User Story 3 — GitHub Actions Workflow for Agent Creation (Priority: P3)

**Goal**: Manual `workflow_dispatch` runs scaffolding and opens PR

**Independent Test**: Verify workflow YAML is valid; the workflow can be tested by triggering manually in the GitHub Actions UI

### Implementation for User Story 3

- [X] T033 [US3] Create `.github/workflows/create-agent.yml` — `workflow_dispatch` with `agent_name` (required) and `model` (default `gpt-4o`) inputs; permissions `contents: write` + `pull-requests: write`; steps: checkout, setup-python 3.11, run scaffolding script, create branch `scaffold/{agent_name}`, commit, push, `gh pr create` per GHA contract
- [X] T034 [US3] Update `docs/scaffolding-guide.md` GitHub Actions section — add link to workflow, describe how to trigger, what the PR contains

**Checkpoint**: All three creation modes (CLI, YAML, GHA) are implemented and documented.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, linting, and cleanup

- [X] T035 Run full test suite: `pytest tests/ -m "not integration" -v` — verify no existing tests broken
- [X] T036 Run linting on all new/modified files: `black --check . && isort --check . && flake8 .`
- [X] T037 Run quickstart.md validation — execute the Quick Start commands from `specs/004-agent-scaffolding/quickstart.md` and verify expected output

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 for script file to exist) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — core CLI scaffolding
- **User Story 2 (Phase 4)**: Depends on Phase 3 (reuses scaffold pipeline) — YAML input mode
- **User Story 4 (Phase 5)**: Depends on Phase 3 (needs working CLI to document accurately) — can run in parallel with Phase 4
- **User Story 3 (Phase 6)**: Depends on Phase 3 (workflow calls the script) — can run in parallel with Phases 4 and 5
- **Polish (Phase 7)**: Depends on all phases complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — no dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (extends the same `main()` function) — adds `--from-file` to existing pipeline
- **User Story 4 (P2)**: Depends on US1 (documents CLI output) — can run in parallel with US2
- **User Story 3 (P3)**: Depends on US1 (workflow calls the script) — can run in parallel with US2 and US4

### Within Each User Story

- Tests written first, verify they fail
- Templates before generation functions
- Generation functions before orchestration
- Orchestration before integration testing

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Phase 3 (US1) completes, US2, US4, and US3 can all start in parallel
- All tests within a user story marked [P] can run in parallel
- Template functions within US1 marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T008: "test_validate_name_valid + test_validate_name_invalid"
Task T009: "test_name_derivation"
Task T010: "test_scaffold_creates_agent_directory"
Task T011: "test_scaffold_creates_test_directory"
Task T012: "test_scaffold_updates_registry"
Task T013: "test_scaffold_rejects_existing_agent"

# Launch both template groups together:
Task T014: "Agent file templates (_template_config, _template_instructions, ...)"
Task T015: "Test file templates (_template_conftest, _template_test_tools, ...)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T007)
3. Complete Phase 3: User Story 1 (T008–T021)
4. **STOP and VALIDATE**: Run `python scripts/create_agent.py --name test-agent` and verify output
5. Deploy/demo if ready — developer can scaffold agents with `--name`

### Incremental Delivery

1. Setup + Foundational → Script skeleton ready
2. User Story 1 → CLI `--name` mode works → MVP!
3. User Story 2 → YAML `--from-file` mode works → CI-friendly
4. User Story 4 → README + guide updated → Discoverable and documented
5. User Story 3 → GHA workflow → Fully automated
6. Polish → All tests pass, linting clean

### Parallel Team Strategy

With multiple developers after US1 is complete:

- Developer A: User Story 2 (YAML mode)
- Developer B: User Story 4 (Documentation)
- Developer C: User Story 3 (GHA workflow)

All three are independent and can merge separately.

---

## Notes

- [P] tasks = different files or independent functions, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- The script uses NO project imports — it is standalone (stdlib only)
- Generated code must pass `black`, `isort`, and `flake8` checks
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
