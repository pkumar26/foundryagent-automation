# Contract: Documentation — README Update + Scaffolding Guide

**Files**: `README.md` (modified), `docs/scaffolding-guide.md` (new), `notebooks/03_scaffold_agent.ipynb` (new)  
**Type**: User-facing documentation  
**Date**: 2026-03-19

## README.md Changes

### "Adding a New Agent" Section

**Current** (manual 3-step process):
```markdown
## Adding a New Agent

1. Create folder: `agents/<new_agent>/` with `config.py`, `instructions.md`, `tools/`, `integrations/`
2. Add one entry to `agents/registry.py`
3. Deploy: `python scripts/deploy_agent.py --agent <new-agent>`

Zero changes to existing agents or shared code required.
```

**Updated** (multi-method with link to guide):
```markdown
## Adding a New Agent

### Automated (Recommended)

```bash
# Scaffold a new agent with one command
python scripts/create_agent.py --name my-agent

# Or specify a model
python scripts/create_agent.py --name my-agent --model gpt-4o-mini

# Or use a YAML input file
python scripts/create_agent.py --from-file agent-config.yaml
```

This generates the full agent directory (`agents/my_agent/`), test stubs (`tests/my_agent/`), and registry entry — ready to deploy immediately.

See the [Scaffolding Guide](docs/scaffolding-guide.md) for YAML format, customisation, FAQ, and troubleshooting.

### Manual

1. Create folder: `agents/<new_agent>/` with `config.py`, `instructions.md`, `tools/`, `integrations/`
2. Add one entry to `agents/registry.py`
3. Deploy: `python scripts/deploy_agent.py --agent <new-agent>`

Zero changes to existing agents or shared code required.
```

### CI/CD Table

Add row:
```
| `create-agent.yml` | Manual dispatch | Scaffold new agent + open PR |
```

### Architecture Tree

Add entries:
```
scripts/
├── deploy_agent.py     # CLI deploy script
└── create_agent.py     # CLI agent scaffolding

docs/                   # Guides and reference documentation
```

## docs/scaffolding-guide.md Structure

### Required Sections

| # | Section | Purpose |
|---|---------|---------|
| 1 | Overview | One-paragraph summary of what the tool does |
| 2 | Prerequisites | Python version, repo state, activated venv |
| 3 | Quick Start | Simplest `--name` command + what appears |
| 4 | CLI Reference | All flags: `--name`, `--model`, `--from-file`, `--help` |
| 5 | YAML Input Reference | Schema table, example file, validation rules |
| 6 | GitHub Actions | How to trigger `create-agent.yml`, what inputs it accepts, what the PR contains |
| 7 | What Gets Generated | Directory tree with annotations for each file |
| 8 | Customise Your Agent | Step-by-step: edit instructions, add tools, update config, write tests |
| 9 | FAQ | ≥5 entries covering rename, delete, multiple tools, model change, integration enable |
| 10 | Troubleshooting | Table of error messages → cause → resolution, ≥5 entries |

### Badges (section-specific)

The guide should include contextual shields.io badges:
```markdown
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?logo=python&logoColor=white)
![CLI Tool](https://img.shields.io/badge/CLI-create__agent.py-green?logo=gnubash&logoColor=white)
```

### FAQ Entries (minimum)

1. How do I rename an agent after scaffolding?
2. How do I delete a scaffolded agent?
3. How do I add more tools to my agent?
4. How do I change the model after creation?
5. How do I enable knowledge source or GitHub MCP integration?
6. Can I scaffold multiple agents at once?

### Troubleshooting Entries (minimum)

| Error Message | Cause | Resolution |
|---------------|-------|------------|
| `Invalid agent name '...'` | Name not in kebab-case | Use lowercase with hyphens: `my-agent` |
| `Agent '...' already exists` | Directory/registry conflict | Choose a different name or delete existing |
| `Input file not found` | Bad `--from-file` path | Check file path and existence |
| `Input file missing required field: 'name'` | YAML missing name | Add `name: your-agent` to YAML |
| `Permission denied` | File system permissions | Check write access to `agents/` and `tests/` |
