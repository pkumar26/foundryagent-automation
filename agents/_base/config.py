"""Base configuration for all agents using pydantic-settings."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class FoundryBaseConfig(BaseSettings):
    """Shared configuration base for all agents.

    Reads from environment variables and .env files.
    Each agent extends this class with agent-specific settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    foundry_project_connection_string: str
    environment: Literal["dev", "qa", "prod"] = "dev"
    azure_key_vault_name: str = ""
