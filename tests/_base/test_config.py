"""Unit tests for FoundryBaseConfig."""

import os
from unittest.mock import patch

import pytest

from agents._base.config import FoundryBaseConfig


class TestFoundryBaseConfig:
    """Tests for the base configuration class."""

    def test_loads_from_env_vars(self):
        """Config should load from environment variables."""
        env = {
            "AZURE_AI_PROJECT_ENDPOINT": "https://test-endpoint.services.ai.azure.com",
            "ENVIRONMENT": "qa",
            "AZURE_KEY_VAULT_NAME": "my-kv",
        }
        with patch.dict(os.environ, env, clear=False):
            config = FoundryBaseConfig()
            assert config.azure_ai_project_endpoint == "https://test-endpoint.services.ai.azure.com"
            assert config.environment == "qa"
            assert config.azure_key_vault_name == "my-kv"

    def test_default_values(self):
        """Config should use defaults when env vars are not set."""
        env = {"AZURE_AI_PROJECT_ENDPOINT": "https://test-endpoint.services.ai.azure.com"}
        with patch.dict(os.environ, env, clear=False):
            config = FoundryBaseConfig()
            assert config.environment == "dev"
            assert config.azure_key_vault_name == ""

    def test_missing_required_field_raises(self):
        """Config should fail when required fields are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):
                FoundryBaseConfig(_env_file=None)
