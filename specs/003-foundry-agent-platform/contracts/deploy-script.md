# Contract: Deploy Script

**Feature**: 003-foundry-agent-platform  
**Module**: `scripts/deploy_agent.py`  
**Consumers**: Developers (CLI), CI/CD pipeline

---

## Purpose

CLI entry point for deploying one or all registered agents. Iterates the agent registry, instantiates each agent's config, and calls its factory function. Reports per-agent success/failure. One agent's failure does not block others.

## Interface

```
Usage: python scripts/deploy_agent.py [--name <name> | --all]

Options:
  --name <name>     Deploy a single agent by name (must exist in registry)
  --all             Deploy all registered agents
  -h, --help        Show help and exit
```

## Behaviour Contract

| Input | Action | Exit Code |
|-------|--------|-----------|
| `--name <name>` (exists) | Deploy single agent | 0 on success, 1 on failure |
| `--name <name>` (not in registry) | Print error with available names, exit | 1 |
| `--all` (registry non-empty) | Deploy each agent; continue on individual failure | 0 if all succeed, 1 if any fail |
| `--all` (registry empty) | Print warning: "No agents registered" | 1 |
| No arguments | Print usage and exit | 1 |
| `--name` + `--all` | Print error: mutually exclusive | 1 |

## Output Contract

Per-agent output during deployment:

```
[deploy] Deploying agent 'my-agent'...
[deploy] ✓ Agent 'my-agent' deployed successfully (id: asst_abc123)
```

On failure:

```
[deploy] Deploying agent 'my-agent'...
[deploy] ✗ Agent 'my-agent' failed: <error message>
```

Summary at end:

```
[deploy] Summary: 2/3 agents deployed successfully
[deploy]   ✓ agent-1
[deploy]   ✓ agent-2
[deploy]   ✗ agent-3: ConnectionError: ...
```

## Error Isolation

Each agent deployment is wrapped in its own try/except. Exceptions from one agent are caught, logged, and the loop continues to the next agent. The script's exit code reflects whether ALL deployments succeeded (0) or ANY failed (1).

## Environment

The script reads configuration from environment variables (via pydantic-settings). The `FOUNDRY_PROJECT_CONNECTION_STRING` must be set. All other settings have defaults in each agent's config class.
