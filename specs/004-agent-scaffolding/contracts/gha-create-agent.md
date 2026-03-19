# Contract: GitHub Actions Workflow — Create Agent

**File**: `.github/workflows/create-agent.yml`  
**Type**: CI/CD workflow  
**Date**: 2026-03-19

## Trigger

Manual dispatch only (`workflow_dispatch`).

### Inputs

| Input | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `agent_name` | string | Yes | — | Agent name in kebab-case |
| `model` | string | No | `gpt-4o` | Model name for the agent |

## Permissions

```yaml
permissions:
  contents: write
  pull-requests: write
```

## Job: scaffold-agent

**Runs on**: `ubuntu-latest`

### Steps

| Step | Action | Description |
|------|--------|-------------|
| 1 | `actions/checkout@v4` | Checkout repository |
| 2 | `actions/setup-python@v5` | Set up Python 3.11 |
| 3 | Run scaffolding | `python scripts/create_agent.py --name ${{ inputs.agent_name }} --model ${{ inputs.model }}` |
| 4 | Create branch | `git checkout -b scaffold/${{ inputs.agent_name }}` |
| 5 | Commit | `git add . && git commit -m "feat: scaffold agent ${{ inputs.agent_name }}"` |
| 6 | Push | `git push origin scaffold/${{ inputs.agent_name }}` |
| 7 | Create PR | `gh pr create --title "feat: add agent ${{ inputs.agent_name }}" --body "..."` |

### Error Handling

- If the scaffolding script exits non-zero, the workflow fails without creating a branch or PR
- If the branch already exists, the push step fails (no force push)

### Authentication

Uses built-in `GITHUB_TOKEN` — no additional secrets required.

## Output

A pull request is created against `main` containing:
- All scaffolded agent files under `agents/<name>/`
- All scaffolded test files under `tests/<name>/`
- Updated `agents/registry.py` with the new entry
