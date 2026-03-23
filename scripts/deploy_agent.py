#!/usr/bin/env python3
"""CLI script for deploying one or all registered agents."""

import argparse
import logging
import sys

from agents.registry import REGISTRY


def main() -> int:
    """Deploy agents via CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy Azure AI Foundry agents",
        prog="deploy_agent.py",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--name",
        type=str,
        help="Deploy a single agent by name",
    )
    group.add_argument(
        "--all",
        action="store_true",
        dest="deploy_all",
        help="Deploy all registered agents",
    )

    args = parser.parse_args()

    if args.deploy_all:
        return _deploy_all()
    else:
        return _deploy_single(args.name)


def _deploy_single(name: str) -> int:
    """Deploy a single agent by name."""
    try:
        entry = REGISTRY.get_agent(name)
    except KeyError as e:
        print(f"[deploy] ✗ {e}", file=sys.stderr)
        return 1

    return _deploy_agent(entry)


def _deploy_all() -> int:
    """Deploy all registered agents."""
    entries = REGISTRY.list_agents()
    if not entries:
        print("[deploy] ✗ No agents registered", file=sys.stderr)
        return 1

    results: list[tuple[str, bool, str]] = []

    for entry in entries:
        exit_code = _deploy_agent(entry)
        if exit_code == 0:
            results.append((entry.name, True, ""))
        else:
            results.append((entry.name, False, "deployment failed"))

    # Summary
    success_count = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n[deploy] Summary: {success_count}/{total} agents deployed successfully")
    for name, ok, err in results:
        if ok:
            print(f"[deploy]   ✓ {name}")
        else:
            print(f"[deploy]   ✗ {name}: {err}")

    return 0 if success_count == total else 1


def _deploy_agent(entry) -> int:
    """Deploy a single agent entry. Returns 0 on success, 1 on failure."""
    print(f"[deploy] Deploying agent '{entry.name}'...")
    try:
        config = entry.config_class()
        agent = entry.factory(config)
        print(f"[deploy] ✓ Agent '{entry.name}' deployed successfully (id: {agent.id})")
        return 0
    except Exception as e:
        print(f"[deploy] ✗ Agent '{entry.name}' failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(main())
