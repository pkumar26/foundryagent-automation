"""GitHub OpenAPI integration for the doc-assistant agent.

Re-exports the shared GitHub OpenAPI tool from the base integrations module.
To customise, replace the import with your own implementation.
See docs/openapi-integration-guide.md for setup instructions.
"""

from agents._base.integrations.github_openapi import get_github_openapi_tool  # noqa: F401

__all__ = ["get_github_openapi_tool"]
