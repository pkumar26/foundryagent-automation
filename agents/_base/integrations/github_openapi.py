"""Shared GitHub OpenAPI integration — OpenAPI tool for GitHub API access."""

from azure.ai.agents.models import (
    OpenApiConnectionAuthDetails,
    OpenApiConnectionSecurityScheme,
    OpenApiTool,
)

from agents._base.config import FoundryBaseConfig

# Minimal GitHub API spec — covers common operations.
# Add more paths from https://github.com/github/rest-api-description as needed.
GITHUB_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "GitHub API", "version": "1.0.0"},
    "servers": [{"url": "https://api.github.com"}],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
            }
        }
    },
    "security": [{"bearerAuth": []}],
    "paths": {
        "/users/{username}/repos": {
            "get": {
                "operationId": "listUserRepos",
                "summary": "List repositories for a user (not an organization)",
                "parameters": [
                    {
                        "name": "username",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "sort",
                        "in": "query",
                        "schema": {
                            "type": "string",
                            "enum": ["created", "updated", "pushed", "full_name"],
                        },
                    },
                    {
                        "name": "per_page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 30},
                    },
                ],
                "responses": {"200": {"description": "List of repositories"}},
            }
        },
        "/orgs/{org}/repos": {
            "get": {
                "operationId": "listOrgRepos",
                "summary": (
                    "List repositories for an organization."
                    " Use this when the target is a GitHub organization,"
                    " not an individual user."
                ),
                "parameters": [
                    {
                        "name": "org",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "The organization name (e.g. 'Western-Financial-Group')",
                    },
                    {
                        "name": "type",
                        "in": "query",
                        "schema": {
                            "type": "string",
                            "enum": ["all", "public", "private", "forks", "sources", "member"],
                        },
                    },
                    {
                        "name": "sort",
                        "in": "query",
                        "schema": {
                            "type": "string",
                            "enum": ["created", "updated", "pushed", "full_name"],
                        },
                    },
                    {
                        "name": "per_page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 30},
                    },
                ],
                "responses": {"200": {"description": "List of organization repositories"}},
            }
        },
        "/repos/{owner}/{repo}": {
            "get": {
                "operationId": "getRepo",
                "summary": "Get a repository",
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "Repository details"}},
            }
        },
        "/repos/{owner}/{repo}/contents/{path}": {
            "get": {
                "operationId": "getRepoContent",
                "summary": (
                    "Get repository file or directory contents."
                    " Returns file content (base64-encoded)"
                    " or directory listing."
                ),
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                    {
                        "name": "path",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "File or directory path (e.g. 'src/main.py' or 'src/')",
                    },
                    {
                        "name": "ref",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Branch, tag, or commit SHA (defaults to default branch)",
                    },
                ],
                "responses": {
                    "200": {"description": "File content (base64-encoded) or directory listing"}
                },
            }
        },
        "/repos/{owner}/{repo}/git/trees/{tree_sha}": {
            "get": {
                "operationId": "getTree",
                "summary": "Get a Git tree — use with recursive=1 to list all files in a repo",
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                    {
                        "name": "tree_sha",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Tree SHA or branch name (e.g. 'main')",
                    },
                    {
                        "name": "recursive",
                        "in": "query",
                        "schema": {"type": "string", "enum": ["1"]},
                        "description": "Set to 1 for recursive tree listing",
                    },
                ],
                "responses": {"200": {"description": "Tree object with file paths"}},
            }
        },
        "/repos/{owner}/{repo}/issues": {
            "get": {
                "operationId": "listIssues",
                "summary": "List repository issues",
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                    {
                        "name": "state",
                        "in": "query",
                        "schema": {"type": "string", "enum": ["open", "closed", "all"]},
                    },
                ],
                "responses": {"200": {"description": "List of issues"}},
            }
        },
        "/repos/{owner}/{repo}/pulls": {
            "get": {
                "operationId": "listPullRequests",
                "summary": "List pull requests",
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                    {
                        "name": "state",
                        "in": "query",
                        "schema": {"type": "string", "enum": ["open", "closed", "all"]},
                    },
                ],
                "responses": {"200": {"description": "List of pull requests"}},
            }
        },
    },
}


def get_github_openapi_tool(config: FoundryBaseConfig):
    """Return a GitHub OpenAPI tool, or None if disabled.

    Args:
        config: Agent configuration with github_openapi_enabled flag.

    Returns:
        OpenApiTool when enabled, None when disabled.

    Raises:
        ValueError: If enabled but GITHUB_OPENAPI_CONNECTION_ID is not set.
    """
    if not getattr(config, "github_openapi_enabled", False):
        return None

    connection_id = getattr(config, "github_openapi_connection_id", "")
    if not connection_id:
        raise ValueError(
            "GITHUB_OPENAPI_CONNECTION_ID is required when GITHUB_OPENAPI_ENABLED=true. "
            "Create a connection in Azure AI Foundry and set the connection ID."
        )

    auth = OpenApiConnectionAuthDetails(
        security_scheme=OpenApiConnectionSecurityScheme(
            connection_id=connection_id,
        )
    )

    return OpenApiTool(
        name="github",
        description="Query GitHub repositories — list issues, pull requests, and more.",
        spec=GITHUB_SPEC,
        auth=auth,
    )
