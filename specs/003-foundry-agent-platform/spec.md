# Feature Specification: Foundry Agent Platform

**Feature Branch**: `003-foundry-agent-platform`  
**Created**: 2026-03-18  
**Status**: Approved  
**Input**: User description: "Build a production-grade, multi-agent platform using the Azure AI Foundry Agent Service SDK (Python, azure-ai-projects library), hosted serverlessly via Azure AI Foundry. The platform must support multiple agents, each fully self-contained, deployable individually or together across multiple environments (dev, qa, prod) via automated CI/CD using GitHub Actions and Terraform or Bicep. The project must include automated testing and Jupyter notebook onboarding guides. Knowledge source integration (Azure AI Search) and GitHub MCP integration must be architecturally reserved but not yet implemented. Foundry infrastructure provisioning must be optional — users must be able to connect to an existing Foundry project or provision a new one using the new Microsoft Foundry resource model."

## Clarifications

### Session 2026-03-18

- Q: Which Azure RBAC roles should the CI/CD service principal and managed identities receive? → A: Per-resource least-privilege roles — Contributor on resource group, Cognitive Services User on Foundry resource, Key Vault Secrets User on Key Vault — defined as role assignments in Terraform/Bicep, applicable to both service principals and managed identities.
- Q: What polling strategy should the run lifecycle use? → A: SDK built-in polling (e.g., `create_and_process_run()`) with fallback to manual exponential backoff (1s–10s) and configurable timeout (default 120s).
- Q: What naming convention should Azure resources follow across environments? → A: Configurable prefix pattern `{prefix}-{resource}-{env}` (e.g., `myproj-kv-dev`), where `prefix` is a user-defined variable in tfvars/bicepparam. Global uniqueness is the user's responsibility via their chosen prefix.
- Q: How is agent name uniqueness enforced? → A: The agent registry enforces uniqueness at load time — duplicate `AGENT_NAME` values cause a fail-fast error before any deployment begins.
- Q: Should integration tests use a dedicated Foundry project or the environment's project? → A: Same project, prefixed names — tests use the environment's Foundry project with a `test-` prefix on agent names (e.g., `test-{agent}-{timestamp}`) and full teardown, providing practical isolation without extra infrastructure.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Connect to Existing Foundry and Deploy First Agent (Priority: P1)

A developer with an existing Azure AI Foundry project wants to deploy their first agent. They clone the repository, set their Foundry project connection string as an environment variable, run the deploy script targeting a single agent, and verify the agent responds to a test prompt.

**Why this priority**: This is the minimum viable path — a developer must be able to deploy and interact with at least one agent before any other capability matters. It validates the core agent lifecycle (create, run, respond) and the "use existing Foundry" mode that most early adopters will follow.

**Independent Test**: Can be fully tested by cloning the repo, configuring a connection string, running `python scripts/deploy_agent.py --agent <name>`, sending a prompt, and verifying a response. Delivers a working, conversational agent.

**Acceptance Scenarios**:

1. **Given** a developer has a valid Foundry project connection string, **When** they set `FOUNDRY_PROJECT_CONNECTION_STRING` and run `deploy_agent.py --agent agent-name-1`, **Then** the agent is created (or updated idempotently) in the Foundry project and the script exits successfully.
2. **Given** a deployed agent exists, **When** the developer creates a thread, posts a message, and starts a run, **Then** the run completes with status "completed" and a non-empty response is returned.
3. **Given** the deploy script is run a second time for the same agent with updated instructions, **When** it completes, **Then** the existing agent is updated (not duplicated) and reflects the new instructions.

---

### User Story 2 — Add and Deploy a New Agent Independently (Priority: P2)

A developer wants to add a second agent to the platform. They create a new folder under `agents/`, define the agent's config, instructions, and tools, register it in the agent registry, and deploy it — without modifying any existing agent or shared infrastructure.

**Why this priority**: Multi-agent extensibility is the primary architectural differentiator. Proving that a new agent can be added and deployed in isolation validates the self-contained agent pattern and the registry design.

**Independent Test**: Can be fully tested by adding a new agent folder, registering it, running `deploy_agent.py --agent <new-agent>`, and verifying it responds independently. No changes to existing agents required.

**Acceptance Scenarios**:

1. **Given** the developer creates a new folder `agents/<new-agent>/` with config, instructions, and tools, **When** they register it in `registry.py` and run `deploy_agent.py --agent <new-agent>`, **Then** the new agent is created in the Foundry project.
2. **Given** two agents are registered, **When** the developer runs `deploy_agent.py --all`, **Then** both agents are deployed, and one failing does not block the other.
3. **Given** a developer requests deployment of a non-existent agent name, **When** they run `deploy_agent.py --agent unknown`, **Then** the script fails fast with a clear error message.

---

### User Story 3 — Automated CI/CD Deployment Across Environments (Priority: P3)

A team wants to deploy agents automatically to dev on every push to main, and promote to qa/prod via manual workflow dispatch. They configure GitHub Actions with OIDC authentication and choose either Terraform or Bicep for infrastructure.

**Why this priority**: Automated, repeatable deployments are essential for production readiness. This story validates the full pipeline including infrastructure provisioning, agent deployment, and environment promotion.

**Independent Test**: Can be tested by pushing a change to main and observing that the GitHub Actions workflow provisions infrastructure (if needed), deploys agents to dev, and runs integration tests. Manual dispatch to qa/prod can be verified separately.

**Acceptance Scenarios**:

1. **Given** a push to main, **When** the deploy pipeline triggers, **Then** shared infrastructure is provisioned (or unchanged if already present), all registered agents are deployed to dev, and integration tests pass.
2. **Given** a manual workflow dispatch with `environment=qa`, `infra_tool=terraform`, and `agent_target=all`, **When** the pipeline runs, **Then** infrastructure is provisioned in qa and all agents are deployed to qa.
3. **Given** a pipeline run with `use_existing_foundry=false`, **When** provisioning runs, **Then** a new Foundry resource (CognitiveServices/AIServices) and project are created, and the project connection string is available to downstream steps.
4. **Given** a pipeline run with `use_existing_foundry=true`, **When** provisioning runs, **Then** Foundry provisioning is skipped entirely and the connection string is read from the environment-specific GitHub secret.

---

### User Story 4 — Onboard via Jupyter Notebooks (Priority: P4)

A Python developer new to Azure AI Foundry Agent Service wants to learn by running interactive notebooks. They open the setup notebook, connect to a Foundry project, then open the build-and-run notebook to create and interact with an agent.

**Why this priority**: Notebooks lower the onboarding barrier and serve as living documentation. They are essential for adoption but depend on the core agent implementation being functional first.

**Independent Test**: Can be tested by opening each notebook in Jupyter, running all cells top-to-bottom, and verifying each cell produces the expected output without errors.

**Acceptance Scenarios**:

1. **Given** a developer opens `01_setup_and_connect.ipynb` and has a valid connection string, **When** they run the Mode A cells, **Then** an `AIProjectClient` is initialised and connection is verified.
2. **Given** a developer opens `02_build_and_run_agent.ipynb`, **When** they run all cells, **Then** an agent is created, a thread is created, a message is posted, a run completes, and a response is displayed.
3. **Given** a developer changes the `AGENT_NAME` variable at the top of a notebook, **When** they re-run, **Then** the notebook operates against the new agent without any other code changes.

---

### User Story 5 — Provision New Foundry Infrastructure from Scratch (Priority: P5)

A team starting fresh (no existing Foundry resource) wants to provision all Azure infrastructure — including a new Foundry resource and project — using their choice of Terraform or Bicep, then deploy agents on top.

**Why this priority**: While most users will connect to existing Foundry projects initially, greenfield provisioning is required for full self-service. This validates the "create new" infrastructure path.

**Independent Test**: Can be tested by running `terraform apply` or `az deployment` with `use_existing_foundry=false`, verifying the Foundry resource and project exist in Azure, then deploying an agent to the new project.

**Acceptance Scenarios**:

1. **Given** `use_existing_foundry=false` and a Terraform workspace, **When** `terraform apply` runs with dev.tfvars, **Then** a resource group, Key Vault, Foundry resource (CognitiveServices/AIServices), and Foundry project are created, and the project connection string is output.
2. **Given** `use_existing_foundry=false` and a Bicep deployment, **When** `az deployment` runs with dev.bicepparam, **Then** the same resources are created with identical naming.
3. **Given** `enable_knowledge_source=true`, **When** infrastructure is provisioned, **Then** an Azure AI Search resource is also created.
4. **Given** `enable_knowledge_source=false` (default), **When** infrastructure is provisioned, **Then** no Azure AI Search resource is created.

---

### User Story 6 — Run Tests Locally and in CI (Priority: P6)

A developer wants to run unit tests locally without Azure credentials, and integration tests in CI against a live Foundry project. The test suite must mirror the agent structure and support running tests for a single agent.

**Why this priority**: Testing confidence is essential for safe deployments but is a verification layer on top of working agents and pipelines.

**Independent Test**: Can be tested by running `pytest` locally (unit tests pass without credentials) and in CI with credentials (integration tests pass with a live Foundry project).

**Acceptance Scenarios**:

1. **Given** no Azure credentials are configured, **When** a developer runs `pytest` (excluding integration markers), **Then** all unit tests pass and no Azure calls are made.
2. **Given** `FOUNDRY_PROJECT_CONNECTION_STRING` is set, **When** `pytest -m integration` runs, **Then** integration tests create temporary agents and threads, assert correct responses, and clean up all resources.
3. **Given** a developer runs `pytest -m agent_name_1`, **When** tests execute, **Then** only tests for that specific agent run.

---

### Edge Cases

- What happens when the Foundry project connection string is invalid or expired? The system must fail fast with a clear authentication error, not silently hang or produce cryptic stack traces.
- What happens when an agent's instructions file is missing or empty? The agent factory must reject the request with a descriptive error before making any API call.
- What happens when two CI/CD runs deploy the same agent simultaneously? The idempotent create-or-update pattern must ensure one wins cleanly without corrupting agent state.
- What happens when Azure Key Vault is unreachable during deployment? The deploy script must surface the connectivity error and fail for that agent without blocking others.
- What happens when a Foundry run enters a "failed" or "cancelled" terminal state? The run lifecycle must detect this, log the failure reason, and raise an error — not loop indefinitely.
- What happens when `deploy_agent.py --all` is run but the registry is empty? The script must exit with a clear warning that no agents are registered.
- What happens when the Terraform remote state backend (Azure Blob Storage) is not initialised? Terraform must fail with a clear message before attempting any resource operations.

## Requirements *(mandatory)*

### Functional Requirements

#### Agent Implementation

- **FR-001**: System MUST provide an agent registry that maps agent names to their configuration and factory, supporting list-all, lookup-by-name, and fail-fast on unknown names. The registry MUST enforce agent name uniqueness at load time — if two agent entries resolve to the same `AGENT_NAME` value, the registry MUST raise an error before any deployment begins.
- **FR-002**: System MUST implement a shared agent factory function (`create_or_update_agent`) that creates new agents or idempotently updates existing agents by name, model, instructions, and tools.
- **FR-003**: Each agent MUST be fully self-contained in its own folder with config, instructions, tools, and integration stubs — adding a new agent requires only creating its folder and registering it.
- **FR-004**: System MUST provide a base configuration class with shared settings (Foundry connection string, environment name, Key Vault name) that each agent extends with agent-specific settings.
- **FR-005**: Each agent MUST store its instructions as a versioned markdown file within its folder, treated as a code artifact under version control.
- **FR-006**: System MUST expose a singleton client initialisation function using `DefaultAzureCredential` and the Foundry project connection string, shared across all agents.
- **FR-007**: System MUST implement the full thread-and-run lifecycle: create thread, post message, start run, poll until terminal status, retrieve response, and handle failure/cancellation with clear errors. Polling MUST use the SDK's built-in `create_and_process_run()` method when available, falling back to a manual poll loop with exponential backoff (1s initial, 10s cap) and a configurable timeout (default 120s).

#### Integration Stubs

- **FR-008**: Each agent MUST include a knowledge source stub (`integrations/knowledge.py`) that returns `None` when `KNOWLEDGE_SOURCE_ENABLED` is false, with reserved environment variables for search endpoint and index name.
- **FR-009**: Each agent MUST include a GitHub MCP stub (`integrations/github_mcp.py`) that returns `None` when `GITHUB_MCP_ENABLED` is false, with reserved environment variables `GITHUB_MCP_ENDPOINT` (MCP server endpoint) and `GITHUB_MCP_TOKEN_SECRET_NAME` (Key Vault secret name for the GitHub PAT).
- **FR-010**: The agent factory MUST conditionally append knowledge and GitHub MCP tools to the agent's tool list based on their respective feature flags.

#### Infrastructure

- **FR-011**: Infrastructure provisioning MUST support two modes: "use existing Foundry" (default, skips Foundry provisioning) and "create new Foundry" (provisions a new Foundry resource using the CognitiveServices/AIServices model).
- **FR-012**: When creating a new Foundry resource, the system MUST use the new Microsoft Foundry resource model (`Microsoft.CognitiveServices/accounts`, `kind=AIServices`, with project management enabled and a unique custom subdomain) — never the classic Hub+Project model.
- **FR-013**: Infrastructure MUST always provision a resource group and Azure Key Vault, and optionally provision Azure AI Search when `enable_knowledge_source` is true.
- **FR-014**: Both Terraform and Bicep paths MUST produce identical Azure environments, with environment differences expressed solely through tfvars/bicepparam files. All Azure resources MUST follow the naming convention `{prefix}-{resource}-{env}` (e.g., `myproj-kv-dev`), where `prefix` is a configurable variable defined in each environment's tfvars/bicepparam file. Global uniqueness of resource names is the user's responsibility via their chosen prefix.
- **FR-015**: Infrastructure MUST output the project connection string, resource group name, and Key Vault name for consumption by the deploy pipeline.
- **FR-016**: Terraform MUST use a remote state backend (Azure Blob Storage) for state management.
- **FR-016a**: Infrastructure MUST define per-resource RBAC role assignments for the CI/CD identity (service principal or managed identity): **Contributor** on the resource group, **Cognitive Services User** on the Foundry resource, and **Key Vault Secrets User** on the Key Vault. Both Terraform and Bicep paths MUST include these role assignments.

#### CI/CD

- **FR-017**: A test pipeline MUST trigger on pull requests and pushes to main, running unit tests, linting (Black, isort, flake8), and formatting checks — no Azure credentials required.
- **FR-018**: A deploy pipeline MUST accept inputs for environment (dev/qa/prod), infrastructure tool (terraform/bicep), Foundry mode (use existing or create new), and agent target (all or specific name).
- **FR-019**: The deploy pipeline MUST resolve the agent target against the registry, fail fast if an unknown agent is specified, and deploy each agent independently — one agent failing MUST NOT block others.
- **FR-020**: CI/CD authentication MUST use OIDC (Workload Identity Federation) with per-environment credentials — no client secrets.
- **FR-021**: Dev deployments MUST trigger automatically on push to main; qa and prod MUST require manual workflow dispatch, with prod requiring an additional GitHub Environment approval gate.

#### Testing

- **FR-022**: Unit tests MUST cover tool functions, config loading, agent factory logic, registry lookups, and integration stub behaviour — all without Azure credentials (SDK mocked).
- **FR-023**: Integration tests MUST cover the full agent create/run/assert cycle against a live Foundry project, with temporary agent and thread creation/teardown per test. Test agents MUST use a `test-` name prefix (e.g., `test-{agent}-{timestamp}`) to avoid collisions with deployed agents in the same Foundry project.
- **FR-024**: Tests MUST be organised to mirror the `agents/` folder structure, with per-agent pytest markers enabling targeted test runs.
- **FR-025**: Integration tests MUST be skipped automatically when `FOUNDRY_PROJECT_CONNECTION_STRING` is not set.

#### Notebooks

- **FR-026**: The setup notebook MUST guide users through both Foundry modes (use existing vs. create new), with clearly labelled sections and connection verification.
- **FR-027**: The build-and-run notebook MUST walk users through creating an agent, running it, and demonstrating a function tool — runnable top-to-bottom without external dependencies beyond the Foundry connection.
- **FR-028**: Both notebooks MUST be agent-agnostic via a configurable `AGENT_NAME` variable at the top, allowing users to switch between agents by changing one value.

#### Deploy Script

- **FR-029**: The deploy script MUST accept `--agent <name>` to deploy a single agent or `--all` to deploy every registered agent, iterating through the registry.
- **FR-030**: The deploy script MUST log success or failure per agent, and one agent's failure MUST NOT prevent others from deploying.

### Key Entities

- **Agent**: A named, self-contained AI entity with its own configuration, instructions, model assignment, tools, and integration stubs. Identified by a unique name per environment. Managed through the agent registry.
- **Agent Registry**: A central mapping of agent names to their configuration classes and factory functions. Used by deploy scripts and CI/CD to discover, validate, and iterate over agents.
- **Agent Configuration**: A settings object (extending a shared base) that holds all environment variables and defaults for a specific agent — connection string, model name, instructions path, feature flags, and agent-specific variables.
- **Thread**: A conversation context created per interaction session. Contains messages and is associated with a specific agent run.
- **Run**: An execution instance where an agent processes a thread's messages. Has a lifecycle with terminal statuses (completed, failed, cancelled).
- **Tool**: A callable function registered with an agent that extends its capabilities. Scoped to the agent that uses it, with shared utilities available from the base module.
- **Foundry Resource**: The Azure-side container for AI services, provisioned using the CognitiveServices/AIServices model. Hosts one or more Foundry projects.
- **Foundry Project**: A logical workspace within a Foundry resource where agents are deployed and managed. Identified by a connection string.
- **Integration Stub**: A placeholder module within each agent that returns `None` when its feature flag is disabled. Designed to be replaced with a real implementation without restructuring.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can deploy their first agent and receive a response to a test prompt within 15 minutes of cloning the repository (given an existing Foundry project).
- **SC-002**: Adding a new agent requires changes to exactly two locations: the new agent's folder and a single line in the registry — zero changes to existing agents, shared code, or infrastructure.
- **SC-003**: 100% of unit tests pass without any Azure credentials configured, and 100% of integration tests pass against a live Foundry project before any promotion to qa or prod.
- **SC-004**: One agent failing to deploy does not affect the deployment of any other agent — verified by the deploy pipeline completing and reporting per-agent status.
- **SC-005**: Both Terraform and Bicep produce identical Azure environments — verified by deploying with each tool and comparing resource names, configuration, and outputs.
- **SC-006**: A developer new to Azure AI Foundry can complete both onboarding notebooks top-to-bottom without external help, connecting to a Foundry project and running an agent successfully.
- **SC-007**: The CI/CD pipeline deploys to dev automatically on every push to main, with manual promotion to qa and prod, and no client secrets used anywhere in the pipeline.
- **SC-008**: Switching between "use existing Foundry" and "create new Foundry" modes requires changing only a single boolean input — no code changes, no pipeline modifications.
- **SC-009**: Integration test runs create and tear down all temporary resources (agents, threads) — no orphaned resources remain after a test suite completes.

## Assumptions

- Users have an active Azure subscription with sufficient permissions to create resource groups, Key Vaults, and CognitiveServices resources.
- The Azure AI Foundry Agent Service supports the create-or-update-by-name pattern for idempotent agent management via the `azure-ai-projects` SDK.
- GitHub Actions OIDC (Workload Identity Federation) is configured per environment with the appropriate Azure AD app registrations.
- The new Microsoft Foundry resource model (`CognitiveServices/AIServices` with `--allow-project-management`) is generally available and supported by both Terraform `azurerm` provider (>= 4.0) and Bicep.
- Python 3.11+ is available in all CI/CD runner environments and developer workstations.
- Developers are comfortable with basic Git operations, Python virtual environments, and environment variable configuration.
