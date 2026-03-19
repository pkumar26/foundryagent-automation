# foundryagent-automation Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-19

## Active Technologies
- Python 3.11 + Python standard library only (argparse, pathlib, textwrap, re); pydantic-settings (existing, for generated config classes) (004-agent-scaffolding)
- Filesystem — generates Python source files and Markdown (004-agent-scaffolding)

- Python 3.11+ + azure-ai-projects (AIProjectClient, AgentsClient, FunctionTool, ThreadMessage, Run, RunStatus), azure-identity (DefaultAzureCredential), pydantic-settings (003-foundry-agent-platform)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 004-agent-scaffolding: Added Python 3.11 + Python standard library only (argparse, pathlib, textwrap, re); pydantic-settings (existing, for generated config classes)
- 004-agent-scaffolding: Added Python 3.11 + Python standard library only (argparse, pathlib, textwrap, re); pydantic-settings (existing, for generated config classes)

- 003-foundry-agent-platform: Added Python 3.11+ + azure-ai-projects (AIProjectClient, AgentsClient, FunctionTool, ThreadMessage, Run, RunStatus), azure-identity (DefaultAzureCredential), pydantic-settings

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
