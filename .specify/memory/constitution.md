<!--
  Sync Impact Report
  ==================
  Version change: (template) → 1.0.0
  Bump rationale: Initial ratification — MAJOR version 1.0.0.

  Modified principles:
    - [PRINCIPLE_1_NAME] → I. Coding Standards (new)
    - [PRINCIPLE_2_NAME] → II. Architecture (new)
    - [PRINCIPLE_3_NAME] → III. Testing (new)
    - [PRINCIPLE_4_NAME] → IV. CI/CD and Collaboration (new)
    - [PRINCIPLE_5_NAME] → V. AI Agent Governance (new)

  Added sections:
    - Project Identity (preamble)
    - Documentation
    - Extensibility Contract
    - Governance

  Removed sections: (none — initial creation)

  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ no update needed
      (Constitution Check section is dynamically filled at plan time)
    - .specify/templates/spec-template.md ✅ no update needed
      (generic spec structure, no constitution-specific references)
    - .specify/templates/tasks-template.md ✅ no update needed
      (generic task structure, no constitution-specific references)

  Follow-up TODOs: (none)
-->

# FoundryAgent Automation Constitution

This project builds and operates production-grade AI Agents
using Azure AI Foundry. All decisions MUST prioritize developer
experience, reliability, and safe production deployments.

This constitution applies to all contributors, human and AI.
It MUST guide all `/specify`, `/plan`, and `/tasks` outputs
for this project.

## Core Principles

### I. Coding Standards

- Python is the primary language. All code MUST be typed,
  linted, and formatted.
- Code MUST be readable by a developer unfamiliar with the
  codebase — clarity beats cleverness.
- Every public function, class, and module MUST have a
  docstring.
- Secrets and credentials MUST never be hardcoded — always
  sourced from environment variables or a secrets manager.
- Feature flags MUST be used to gate incomplete or optional
  capabilities rather than commenting out code.

### II. Architecture

- Infrastructure MUST be declarative and version-controlled
  alongside code.
- All environments (dev, qa, prod) MUST be structurally
  identical — differences are configuration only.
- The same codebase MUST be deployable to all environments
  using configuration and IaC, without environment-specific
  code forks.
- No manual changes to any environment. Everything goes
  through CI/CD.
- Design for extensibility: new capabilities (e.g. knowledge
  sources, new tools) MUST be addable without restructuring
  existing code.
- Prefer managed Azure services over self-hosted equivalents.

### III. Testing

- Every agent behaviour that can be asserted MUST have a test.
- Unit tests MUST NOT require live Azure credentials.
- Integration tests MUST be clearly separated from unit tests
  and skippable in environments where Azure credentials are
  unavailable.
- A pull request MUST NOT be merged if tests are failing.
- Tests are first-class code — they follow the same quality
  standards as production code.

### IV. CI/CD and Collaboration

- All deployments are automated. No human manually runs
  deployment scripts.
- Production deployments require explicit human approval.
- Every deployment to every environment runs the test suite
  first.
- Deployments MUST be idempotent — running the same pipeline
  twice MUST produce the same result.
- Credentials for CI/CD MUST use short-lived tokens (OIDC) —
  no long-lived secrets in pipelines.
- The main branch is always deployable.
- All work happens on feature branches and enters main via
  pull request.
- Pull requests require at least one review before merging.
- Commit messages MUST be descriptive and reference the
  relevant issue or spec where applicable.

### V. AI Agent Governance

- Agents MUST have explicit, version-controlled instructions.
- Agent behaviour changes (instructions, tools, model) are
  treated as code changes — reviewed and deployed through the
  same pipeline.
- Agents MUST be testable in isolation before being deployed
  to higher environments.
- The initial agent design MUST work without custom knowledge
  sources; knowledge integration is an optional extension, not
  a prerequisite.

## Documentation

- Every feature MUST include a notebook-based walkthrough for
  user onboarding.
- READMEs MUST be kept current — outdated documentation is
  treated as a bug.
- Architecture decisions MUST be recorded with their
  rationale, not just the outcome.
- Notebooks are written for a developer new to the project —
  assume no prior context.
- Documentation is expected to evolve with the system, but
  constitutional principles MUST remain stable and only change
  through deliberate revision.

## Extensibility Contract

- Optional capabilities MUST have clearly marked integration
  points in the codebase, even before they are implemented.
- Removing or renaming an integration point is a breaking
  change and requires explicit agreement.
- The knowledge source integration point is a reserved
  extension — its placeholder MUST be preserved until it is
  fully implemented.
- Any future knowledge integration MUST be configurable per
  environment, added without breaking existing agent
  behaviours, and expressed as data/config plus SDK-based
  wiring, not hard-coded logic.

## Governance

- This constitution supersedes all other practices when in
  conflict.
- Amendments require documentation, review, and approval
  before taking effect.
- All PRs and reviews MUST verify compliance with these
  principles.
- Complexity MUST be justified — default to the simplest
  approach that satisfies the constraint.

**Version**: 1.0.0 | **Ratified**: 2026-03-18 | **Last Amended**: 2026-03-18
