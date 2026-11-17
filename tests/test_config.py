"""Tests for config.py configuration module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

import config


def test_default_constants() -> None:
    """Verify default constants and paths."""
    assert isinstance(config.BASE_DIR, Path)
    assert config.CONVERSATION_DIR == config.BASE_DIR / "conversations"
    assert config.CONVERSATION_FILE == config.CONVERSATION_DIR / "chat1.json"
    assert config.EXAMPLE_FILE == config.BASE_DIR / "example.json"
    assert config.DEFAULT_MODEL == "meta/llama-3.1-8b-instruct"
    assert config.DEFAULT_MAX_TOKENS == 512
    assert config.DEFAULT_TIMEOUT == 20.0
    assert config.DEFAULT_SYSTEM_PROMPT == "You are a helpful assistant."


def test_get_api_key_when_present() -> None:
    """Test get_api_key returns key when set in environment."""
    with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key-123"}):
        assert config.get_api_key(required=False) == "test-key-123"
        assert config.get_api_key(required=True) == "test-key-123"


def test_get_api_key_when_missing() -> None:
    """Test get_api_key handles missing key based on required parameter."""
    with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}, clear=False):
        with patch.object(config, "API_KEY", None):
            assert config.get_api_key(required=False) is None
            with pytest.raises(ValueError, match="NVIDIA_API_KEY was not found"):
                config.get_api_key(required=True)


def test_validate_config_success() -> None:
    """Test validate_config returns True when API key is present."""
    with patch.dict(os.environ, {"NVIDIA_API_KEY": "valid-key"}):
        assert config.validate_config(exit_on_error=False) is True
        assert config.validate_config(exit_on_error=True) is True


def test_validate_config_failure_value_error() -> None:
    """Test validate_config raises ValueError when exit_on_error is False."""
    with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}, clear=False):
        with patch.object(config, "API_KEY", None):
            with pytest.raises(ValueError, match="NVIDIA_API_KEY was not found"):
                config.validate_config(exit_on_error=False)


def test_validate_config_failure_system_exit(capsys: pytest.CaptureFixture[str]) -> None:
    """Test validate_config prints error and exits when exit_on_error is True."""
    with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}, clear=False):
        with patch.object(config, "API_KEY", None):
            with pytest.raises(SystemExit) as exc_info:
                config.validate_config(exit_on_error=True)
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "NVIDIA_API_KEY was not found" in captured.out


def test_config_main_execution() -> None:
    """Test running config.py as a script."""
    import runpy

    with patch.dict(os.environ, {"NVIDIA_API_KEY": "valid-key"}):
        # Running the module directly executes __main__ block
        runpy.run_module("config", run_name="__main__")
