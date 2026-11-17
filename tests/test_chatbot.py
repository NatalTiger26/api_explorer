"""Tests for chatbot.py interactive loop and entry point."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import requests

from chatbot import main, run_chat


def test_run_chat_normal_flow() -> None:
    """Test normal conversation turn followed by exit."""
    inputs = ["Hello world", "exit"]

    def input_fn(_: str) -> str:
        return inputs.pop(0)

    printed: list[str] = []

    def print_fn(*args: Any) -> None:
        printed.append(" ".join(str(a) for a in args))

    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    with patch("chatbot.call_model", return_value="Hello human!") as mock_call:
        updated = run_chat(messages, input_fn=input_fn, print_fn=print_fn)

        mock_call.assert_called_once()
        assert len(updated) == 3
        assert updated[1] == {"role": "user", "content": "Hello world"}
        assert updated[2] == {"role": "assistant", "content": "Hello human!"}
        assert any("Exiting and saving the chat." in msg for msg in printed)


def test_run_chat_empty_input_and_quit() -> None:
    """Test handling of whitespace-only input and 'quit' command."""
    inputs = ["   ", "quit"]

    def input_fn(_: str) -> str:
        return inputs.pop(0)

    printed: list[str] = []

    def print_fn(*args: Any) -> None:
        printed.append(" ".join(str(a) for a in args))

    messages = [{"role": "system", "content": "System"}]

    with patch("chatbot.call_model") as mock_call:
        updated = run_chat(messages, input_fn=input_fn, print_fn=print_fn)

        mock_call.assert_not_called()
        assert len(updated) == 1
        assert any("Please type a message before pressing Enter." in m for m in printed)
        assert any("Exiting and saving the chat." in m for m in printed)


def test_run_chat_eof_handling() -> None:
    """Test EOFError on input (Ctrl+D / closed stdin) exits gracefully."""

    def input_fn(_: str) -> str:
        raise EOFError()

    printed: list[str] = []

    def print_fn(*args: Any) -> None:
        printed.append(" ".join(str(a) for a in args))

    messages = [{"role": "system", "content": "System"}]
    updated = run_chat(messages, input_fn=input_fn, print_fn=print_fn)

    assert len(updated) == 1
    assert any("Exiting and saving the chat." in m for m in printed)


def test_run_chat_network_error_rolls_back_message() -> None:
    """Test that network exceptions trigger error handler and roll back user message."""
    inputs = ["Will fail", "exit"]

    def input_fn(_: str) -> str:
        return inputs.pop(0)

    printed: list[str] = []

    def print_fn(*args: Any) -> None:
        printed.append(" ".join(str(a) for a in args))

    messages = [{"role": "system", "content": "System"}]

    timeout_err = requests.exceptions.Timeout("Request timed out")

    with patch("chatbot.call_model", side_effect=timeout_err) as mock_call:
        with patch("chatbot.handle_api_error") as mock_handle:
            updated = run_chat(messages, input_fn=input_fn, print_fn=print_fn)

            mock_call.assert_called_once()
            mock_handle.assert_called_once_with(timeout_err)
            # The failed user message MUST be rolled back: only system message remains
            assert len(updated) == 1
            assert updated[0]["role"] == "system"


def test_run_chat_unexpected_exception_rolls_back_message() -> None:
    """Test that unexpected exceptions trigger recovery and roll back user message."""
    inputs = ["Unexpected error", "exit"]

    def input_fn(_: str) -> str:
        return inputs.pop(0)

    printed: list[str] = []

    def print_fn(*args: Any) -> None:
        printed.append(" ".join(str(a) for a in args))

    messages = [{"role": "system", "content": "System"}]

    with patch("chatbot.call_model", side_effect=KeyError("Missing choice")):
        updated = run_chat(messages, input_fn=input_fn, print_fn=print_fn)

        assert len(updated) == 1
        assert any("An error occurred while communicating with the model" in m for m in printed)


def test_main_clean_exit(tmp_path: Path) -> None:
    """Test main function runs startup, chat loop, and saves history."""
    test_conv_file = tmp_path / "test_chat.json"
    sample_return = [{"role": "system", "content": "done"}]

    with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
        with patch("chatbot.run_chat", return_value=sample_return) as mock_chat:
            exit_code = main(conversation_file=test_conv_file)

            assert exit_code == 0
            mock_chat.assert_called_once()
            assert test_conv_file.exists()


def test_main_with_existing_file_logs_loaded(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test main function notices when conversation file already exists."""
    existing_file = tmp_path / "existing_chat.json"
    existing_file.write_text("[]", encoding="utf-8")

    with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
        with patch("chatbot.run_chat", return_value=[]):
            exit_code = main(conversation_file=existing_file)
            assert exit_code == 0
            captured = capsys.readouterr()
            assert "Loaded previous conversation." in captured.out


def test_main_keyboard_interrupt_saves_history(tmp_path: Path) -> None:
    """Test that KeyboardInterrupt during main preserves history."""
    test_conv_file = tmp_path / "test_chat_interrupt.json"

    with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
        with patch("chatbot.run_chat", side_effect=KeyboardInterrupt):
            exit_code = main(conversation_file=test_conv_file)

            assert exit_code == 0
            assert test_conv_file.exists()
