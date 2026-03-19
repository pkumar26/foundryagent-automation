# Contract: Agent Registry

**Feature**: 003-foundry-agent-platform  
**Module**: `agents/registry.py`  
**Consumers**: `scripts/deploy_agent.py`, CI/CD pipeline, tests

---

## Purpose

Central registry mapping agent names to their configuration classes and factory functions. Used by all deployment and discovery paths.

## Interface

```python
from dataclasses import dataclass
from typing import Callable, Type
from agents._base.config import FoundryBaseConfig


@dataclass(frozen=True)
class AgentRegistryEntry:
    """An entry in the agent registry."""
    name: str
    config_class: Type[FoundryBaseConfig]
    factory: Callable  # Signature: (config: FoundryBaseConfig) -> Agent


class AgentRegistry:
    """Central registry of all agents. Immutable after construction."""

    def __init__(self, entries: list[AgentRegistryEntry]) -> None:
        """Initialise and validate uniqueness."""
        ...

    def list_agents(self) -> list[AgentRegistryEntry]:
        """Return all registered agent entries."""
        ...

    def get_agent(self, name: str) -> AgentRegistryEntry:
        """Return the entry for the given agent name.
        
        Raises:
            KeyError: If no agent with the given name is registered.
                      Message includes the requested name and available names.
        """
        ...

    def validate(self) -> None:
        """Check all invariants. Called during __init__.
        
        Raises:
            ValueError: If duplicate agent names are detected.
                        Message lists all duplicates.
        """
        ...
```

## Registration Pattern

```python
# agents/registry.py — bottom of file
from agents.my_agent.config import MyAgentConfig
from agents._base.agent_factory import create_or_update_agent

REGISTRY = AgentRegistry([
    AgentRegistryEntry(
        name="my-agent",
        config_class=MyAgentConfig,
        factory=create_or_update_agent,
    ),
    # Add new agents here — one line per agent
])
```

## Invariants

1. **Uniqueness**: No two entries may share the same `name`. Enforced at construction time.
2. **Immutability**: Registry is frozen after construction — no add/remove at runtime.
3. **Fail-fast**: `get_agent()` raises immediately with a descriptive message listing available names.

## Error Contract

| Condition | Exception | Message Pattern |
|-----------|-----------|-----------------|
| Duplicate name at init | `ValueError` | `"Duplicate agent name '{name}' in registry. Each agent must have a unique name."` |
| Unknown name lookup | `KeyError` | `"Agent '{name}' not found. Available agents: {', '.join(names)}"` |
| Empty registry (warning) | N/A | `list_agents()` returns `[]` — deploy script handles this |
