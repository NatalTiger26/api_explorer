"""Tests for history.py conversation history management."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from history import load_history, save_history


def test_load_history_nonexistent_file(tmp_path: Path) -> None:
    """Test loading history from a file that does not exist."""
    missing_file = tmp_path / "missing.json"
    history = load_history(missing_file)
    assert len(history) == 1
    assert history[0]["role"] == "system"
    assert history[0]["content"] == "You are a helpful assistant."


def test_load_history_custom_default_prompt(tmp_path: Path) -> None:
    """Test loading history with custom initial system prompt."""
    missing_file = tmp_path / "missing.json"
    history = load_history(missing_file, default_system_prompt="Custom prompt")
    assert len(history) == 1
    assert history[0]["role"] == "system"
    assert history[0]["content"] == "Custom prompt"


def test_load_history_valid_file(tmp_path: Path) -> None:
    """Test loading history from a valid JSON conversation file."""
    valid_file = tmp_path / "chat.json"
    messages = [
        {"role": "system", "content": "System message"},
        {"role": "user", "content": "User message"},
        {"role": "assistant", "content": "Assistant message"},
    ]
    valid_file.write_text(json.dumps(messages), encoding="utf-8")

    loaded = load_history(valid_file)
    assert loaded == messages


def test_load_history_corrupted_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test loading corrupted JSON recovers gracefully."""
    corrupted_file = tmp_path / "corrupt.json"
    corrupted_file.write_text("{this is not valid json", encoding="utf-8")

    history = load_history(corrupted_file)
    assert len(history) == 1
    assert history[0]["role"] == "system"
    captured = capsys.readouterr()
    assert "Conversation file corrupted" in captured.out


def test_load_history_non_list_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test loading JSON that is not a list recovers gracefully."""
    invalid_structure_file = tmp_path / "dict.json"
    invalid_structure_file.write_text(json.dumps({"role": "system"}), encoding="utf-8")

    history = load_history(invalid_structure_file)
    assert len(history) == 1
    assert history[0]["role"] == "system"
    captured = capsys.readouterr()
    assert "Conversation file corrupted" in captured.out


def test_load_and_save_string_path(tmp_path: Path) -> None:
    """Verify both functions accept str paths as well as Path instances."""
    file_path = str(tmp_path / "str_path_test.json")
    messages = [{"role": "system", "content": "Prompt"}, {"role": "user", "content": "Hi"}]

    save_history(file_path, messages)
    loaded = load_history(file_path)
    assert loaded == messages


def test_save_history_creates_parent_directories(tmp_path: Path) -> None:
    """Verify save_history creates missing parent directories automatically."""
    deep_file = tmp_path / "nested" / "subfolder" / "history.json"
    messages = [{"role": "system", "content": "System"}]

    save_history(deep_file, messages)
    assert deep_file.exists()
    assert json.loads(deep_file.read_text(encoding="utf-8")) == messages


def test_save_history_atomic_overwrite(tmp_path: Path) -> None:
    """Verify atomic overwrite maintains valid state on multiple writes."""
    history_file = tmp_path / "history.json"
    messages_v1 = [{"role": "system", "content": "v1"}]
    messages_v2 = [{"role": "system", "content": "v2"}, {"role": "user", "content": "hi"}]

    save_history(history_file, messages_v1)
    assert load_history(history_file) == messages_v1

    save_history(history_file, messages_v2)
    assert load_history(history_file) == messages_v2
    # Ensure no dangling temporary files remain
    temp_files = list(tmp_path.glob(".*.tmp"))
    assert len(temp_files) == 0


def test_load_history_list_with_no_valid_message_dicts(tmp_path: Path) -> None:
    """Verify load_history returns default when list has items without role/content."""
    file_path = tmp_path / "invalid_items.json"
    file_path.write_text(json.dumps([1, 2, "three", {"other": "val"}]), encoding="utf-8")

    loaded = load_history(file_path)
    assert len(loaded) == 1
    assert loaded[0]["role"] == "system"


def test_save_history_failure_cleans_up_temp_file(tmp_path: Path) -> None:
    """Verify that when serialization fails, the temporary file is unlinked."""
    history_file = tmp_path / "failure_history.json"
    bad_messages = [{"unserializable": object()}]

    with pytest.raises(TypeError):
        save_history(history_file, bad_messages)  # type: ignore[arg-type]

    temp_files = list(tmp_path.glob(".*.tmp"))
    assert len(temp_files) == 0
