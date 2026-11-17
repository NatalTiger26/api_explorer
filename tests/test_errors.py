"""Tests for errors.py error handling module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from errors import format_api_error, handle_api_error


def test_timeout_error_formatting() -> None:
    """Verify friendly output for requests Timeout exception."""
    err = requests.exceptions.Timeout("Connection timed out")
    msg = format_api_error(err)
    assert "timed out" in msg
    assert "Please try again." in msg


def test_connection_error_formatting() -> None:
    """Verify friendly output for requests ConnectionError exception."""
    err = requests.exceptions.ConnectionError("Failed to establish a new connection")
    msg = format_api_error(err)
    assert "Could not connect to NVIDIA's servers." in msg
    assert "check your internet connection." in msg


@pytest.mark.parametrize(
    ("status_code", "expected_phrase"),
    [
        (401, "Authentication failed"),
        (403, "Access denied"),
        (404, "The requested model or endpoint could not be found"),
        (429, "Rate limit reached"),
        (500, "NVIDIA's servers are currently experiencing issues"),
        (503, "NVIDIA's servers are currently experiencing issues"),
        (418, "HTTP Error (418)"),
    ],
)
def test_http_error_formatting(status_code: int, expected_phrase: str) -> None:
    """Verify friendly output for specific HTTP status codes."""
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = status_code
    err = requests.exceptions.HTTPError(response=mock_response)

    msg = format_api_error(err)
    assert expected_phrase in msg


def test_http_error_without_response() -> None:
    """Verify fallback when HTTPError lacks a response object."""
    err = requests.exceptions.HTTPError("HTTP error without response", response=None)
    msg = format_api_error(err)
    assert "HTTP Error occurred with no response received" in msg


def test_generic_request_exception() -> None:
    """Verify output for general RequestException."""
    err = requests.exceptions.RequestException("SSL handshake failed")
    msg = format_api_error(err)
    assert "An unexpected network error occurred." in msg
    assert "SSL handshake failed" in msg


def test_general_exception() -> None:
    """Verify fallback for non-requests exceptions."""
    err = RuntimeError("Unexpected runtime breakdown")
    msg = format_api_error(err)
    assert "An unexpected error occurred" in msg
    assert "Unexpected runtime breakdown" in msg


def test_handle_api_error_prints_and_returns(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify handle_api_error prints message and returns identical string."""
    err = requests.exceptions.Timeout("Timed out")
    returned_msg = handle_api_error(err)

    captured = capsys.readouterr()
    assert returned_msg in captured.out
    assert "timed out" in returned_msg
