"""Tests for llm.py LLM completion interface."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from llm import call_model


def _mock_success_response(content: str = "Hello from mock LLM!") -> MagicMock:
    """Helper to build a mocked successful requests.Response."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ]
    }
    return mock_resp


def test_call_model_success() -> None:
    """Test standard call_model round-trip with payload verification."""
    messages = [
        {"role": "system", "content": "You are a test helper."},
        {"role": "user", "content": "Hi!"},
    ]

    mock_resp = _mock_success_response("Greetings!")

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = call_model(
            messages,
            api_key="nvapi-test-key",
            api_url="https://test.api/v1/chat/completions",
        )

        assert result == "Greetings!"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://test.api/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer nvapi-test-key"
        assert kwargs["json"]["messages"] == messages
        assert kwargs["json"]["model"] == "meta/llama-3.1-8b-instruct"
        assert kwargs["json"]["max_tokens"] == 512
        assert kwargs["timeout"] == 20.0


def test_call_model_with_custom_parameters() -> None:
    """Test call_model with custom model identifier, max_tokens, and timeout."""
    mock_resp = _mock_success_response("Custom reply")

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = call_model(
            [{"role": "user", "content": "Ping"}],
            model="custom/nemotron-model",
            max_tokens=1024,
            timeout=35.0,
            api_key="nvapi-key-custom",
        )

        assert result == "Custom reply"
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "custom/nemotron-model"
        assert kwargs["json"]["max_tokens"] == 1024
        assert kwargs["timeout"] == 35.0


def test_call_model_with_session() -> None:
    """Verify call_model uses the provided requests.Session instance."""
    mock_session = MagicMock(spec=requests.Session)
    mock_resp = _mock_success_response("Session reply")
    mock_session.post.return_value = mock_resp

    result = call_model(
        [{"role": "user", "content": "Test"}],
        api_key="nvapi-session-key",
        session=mock_session,
    )

    assert result == "Session reply"
    mock_session.post.assert_called_once()


def test_call_model_missing_api_key_raises_value_error() -> None:
    """Verify call_model raises ValueError when no API key is available."""
    with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}, clear=False):
        with patch("llm.API_KEY", None):
            with pytest.raises(ValueError, match="NVIDIA_API_KEY is required"):
                call_model([{"role": "user", "content": "Test"}], api_key=None)


def test_call_model_http_error_propagates() -> None:
    """Verify HTTP errors from the endpoint raise HTTPError."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 401
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "401 Unauthorized", response=mock_resp
    )

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(requests.exceptions.HTTPError):
            call_model(
                [{"role": "user", "content": "Test"}],
                api_key="invalid-key",
            )


@pytest.mark.parametrize(
    "malformed_payload",
    [
        {},
        {"choices": []},
        {"choices": [{}]},
        {"choices": [{"message": {}}]},
    ],
)
def test_call_model_malformed_response_raises_key_error(
    malformed_payload: dict[str, Any],
) -> None:
    """Verify KeyError is raised when JSON payload is missing expected structure."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = malformed_payload

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(KeyError):
            call_model(
                [{"role": "user", "content": "Test"}],
                api_key="nvapi-key",
            )


def test_call_model_non_json_response_raises_value_error() -> None:
    """Verify ValueError is raised when endpoint returns non-JSON content."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Invalid JSON")

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(ValueError, match="Failed to parse JSON response"):
            call_model(
                [{"role": "user", "content": "Test"}],
                api_key="nvapi-key",
            )


def test_call_model_non_dict_json_raises_value_error() -> None:
    """Verify ValueError is raised when JSON payload is a list or scalar."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = ["unexpected", "list"]

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(ValueError, match="Unexpected API response format"):
            call_model(
                [{"role": "user", "content": "Test"}],
                api_key="nvapi-key",
            )
