"""History management module for API Explorer.

Handles loading, validating, and atomically persisting multi-turn conversation
histories as structured JSON.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from config import DEFAULT_SYSTEM_PROMPT


def _get_default_messages(default_system_prompt: str) -> list[dict[str, str]]:
    """Generate default initial conversation messages.

    Args:
        default_system_prompt: Content for the initial system prompt.

    Returns:
        List containing a single system role message dictionary.
    """
    return [{"role": "system", "content": default_system_prompt}]


def load_history(
    path: str | Path,
    default_system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> list[dict[str, str]]:
    """Load conversation history from a JSON file.

    If the file does not exist, is empty, is corrupted, or contains an invalid
    schema, returns a new conversation with the default system prompt.

    Args:
        path: Path to the JSON conversation file.
        default_system_prompt: The prompt to initialize a new conversation with.

    Returns:
        A list of message dictionaries with 'role' and 'content' keys.
    """
    file_path = Path(path)

    if not file_path.exists():
        return _get_default_messages(default_system_prompt)

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("Conversation file corrupted. Starting a new conversation.")
            return _get_default_messages(default_system_prompt)

        # Validate that elements are dictionaries
        valid_messages: list[dict[str, str]] = []
        for item in data:
            if isinstance(item, dict) and "role" in item and "content" in item:
                valid_messages.append(
                    {
                        "role": str(item["role"]),
                        "content": str(item["content"]),
                    }
                )

        if not valid_messages:
            return _get_default_messages(default_system_prompt)

        return valid_messages

    except FileNotFoundError:
        return _get_default_messages(default_system_prompt)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        print("Conversation file corrupted. Starting a new conversation.")
        return _get_default_messages(default_system_prompt)


def save_history(
    path: str | Path,
    messages: Sequence[dict[str, Any]],
) -> None:
    """Save conversation messages to a JSON file atomically.

    Ensures the parent directory exists, writes to a temporary file,
    flushes to disk, and replaces the target file atomically to prevent
    corruption during abrupt termination.

    Args:
        path: Destination file path for saving conversation history.
        messages: Sequence of message dictionaries to serialize.

    Raises:
        OSError: If writing to the file system fails.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = file_path.with_name(f".{file_path.name}.tmp")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(list(messages), f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        temp_path.replace(file_path)
    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise
