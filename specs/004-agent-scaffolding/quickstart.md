# Quickstart: Agent Scaffolding

## Create a New Agent (CLI)

```bash
# Scaffold with default model (gpt-4o)
python scripts/create_agent.py --name my-agent

# Scaffold with a specific model
python scripts/create_agent.py --name my-agent --model gpt-4o-mini
```

## Create a New Agent (YAML Input)

```bash
# Create a config file
cat > agent-config.yaml << EOF
name: my-agent
model: gpt-4o
EOF

# Scaffold from file
python scripts/create_agent.py --from-file agent-config.yaml
```

## What Gets Generated

```
agents/my_agent/
├── __init__.py
├── config.py              ← Edit model, add config fields
├── instructions.md        ← Write agent instructions
├── integrations/
│   ├── __init__.py
│   ├── github_openapi.py
│   └── knowledge.py
└── tools/
    ├── __init__.py
    └── sample_tool.py     ← Replace with real tools

tests/my_agent/
├── __init__.py
├── conftest.py
├── test_tools.py
├── test_agent_create.py
└── test_agent_run.py
```

Plus: a new entry in `agents/registry.py`.

## Next Steps After Scaffolding

1. **Edit instructions**: Open `agents/my_agent/instructions.md` and write your agent's system prompt
2. **Add tools**: Replace or extend `agents/my_agent/tools/sample_tool.py` with your custom tools
3. **Run tests**: `pytest tests/my_agent/ -v`
4. **Deploy**: `python scripts/deploy_agent.py --agent my-agent`

## Create via GitHub Actions

1. Go to **Actions** → **Create Agent** workflow
2. Click **Run workflow**
3. Enter `agent_name` and optionally `model`
4. A PR is created with the scaffolded agent

## More Information

For YAML input reference, customisation details, FAQ, and troubleshooting, see the [Scaffolding Guide](../../docs/scaffolding-guide.md).
