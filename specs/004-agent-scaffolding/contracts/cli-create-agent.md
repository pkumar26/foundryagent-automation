# Contract: CLI Scaffolding Script

**File**: `scripts/create_agent.py`  
**Type**: CLI tool  
**Date**: 2026-03-19

## Interface

### Command Line Arguments

```
usage: create_agent.py [-h] (--name NAME | --from-file FILE)
                       [--model MODEL]

Scaffold a new Azure AI Foundry agent.

options:
  -h, --help         show this help message and exit
  --name NAME        Agent name in kebab-case (e.g., my-agent)
  --from-file FILE   Path to YAML config file for non-interactive creation
  --model MODEL      Model name (default: gpt-4o)
```

### Mutually Exclusive Groups

- `--name` and `--from-file` are mutually exclusive (one is required)
- `--model` can be combined with `--name` but is ignored when `--from-file` is used (model comes from file)

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success — all files generated, registry updated |
| 1 | Validation error — invalid name, existing agent, bad input file |
| 2 | File system error — permission denied, disk full |

### Output Format

On success, prints a summary to stdout:
```
[scaffold] ✓ Agent 'my-agent' scaffolded successfully
[scaffold]   Created: agents/my_agent/
[scaffold]   Created: tests/my_agent/
[scaffold]   Updated: agents/registry.py
[scaffold]   Files generated: 13
[scaffold]
[scaffold]   Next steps:
[scaffold]   1. Edit agents/my_agent/instructions.md with agent instructions
[scaffold]   2. Add custom tools in agents/my_agent/tools/
[scaffold]   3. Run tests: pytest tests/my_agent/ -v
[scaffold]   4. Deploy: python scripts/deploy_agent.py --agent my-agent
```

On error, prints to stderr:
```
[scaffold] ✗ Agent 'my-agent' already exists at agents/my_agent/
```

### YAML Input File Format

```yaml
name: my-agent
model: gpt-4o
```

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `name` | string | Yes | — |
| `model` | string | No | `gpt-4o` |

### Validation Rules

| Rule | Error Message |
|------|---------------|
| Name must be kebab-case | `Invalid agent name '{name}'. Must be lowercase kebab-case (e.g., my-agent).` |
| Name must not be empty | `Agent name is required.` |
| Agent dir must not exist | `Agent 'my-agent' already exists at agents/my_agent/` |
| Test dir must not exist | `Test directory already exists at tests/my_agent/` |
| Agent not in registry | `Agent 'my-agent' is already registered in agents/registry.py` |
| YAML file must exist | `Input file not found: path/to/file.yaml` |
| YAML must have name | `Input file missing required field: 'name'` |
| Name must be ≤50 chars | `Agent name exceeds maximum length of 50 characters.` |
| Name must not be a reserved word | `Agent name '{name}' is a Python reserved word.` |

## Dependencies

- Python standard library only (`argparse`, `keyword`, `pathlib`, `re`, `sys`, `textwrap`)
- No imports from project code (standalone script)

## Generated Files Contract

The script generates files that conform to the patterns established by existing agents (`code_helper`, `doc_assistant`). See [data-model.md](../data-model.md) for the complete file generation map.
