"""Configuration module for API Explorer.

Handles environment variable loading, default endpoint configuration,
and path definitions for persistent conversation storage.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

# Project directory paths
BASE_DIR: Path = Path(__file__).resolve().parent
CONVERSATION_DIR: Path = BASE_DIR / "conversations"
CONVERSATION_FILE: Path = CONVERSATION_DIR / "chat1.json"
EXAMPLE_FILE: Path = BASE_DIR / "example.json"

# API & LLM Defaults
DEFAULT_MODEL: str = "meta/llama-3.1-8b-instruct"
DEFAULT_MAX_TOKENS: int = 512
DEFAULT_TIMEOUT: float = 20.0
DEFAULT_SYSTEM_PROMPT: str = "You are a helpful assistant."
URL: str = os.environ.get(
    "NVIDIA_API_URL",
    "https://integrate.api.nvidia.com/v1/chat/completions",
)

# API key from environment
API_KEY: str | None = os.environ.get("NVIDIA_API_KEY")

ERROR_MESSAGE: str = (
    "\nERROR: NVIDIA_API_KEY was not found.\n"
    "Create a .env file containing:\n"
    'NVIDIA_API_KEY="nvapi-your-key-here"\n'
    "or export the variable in your terminal."
)


def get_api_key(required: bool = False) -> str | None:
    """Retrieve the NVIDIA API key from the environment.

    Args:
        required: Whether to raise an error if the API key is missing or empty.

    Returns:
        The API key string, or None if not set and not required.

    Raises:
        ValueError: If required is True and the API key is not set or empty.
    """
    key = os.environ.get("NVIDIA_API_KEY", "").strip() or API_KEY
    if required and not key:
        raise ValueError(ERROR_MESSAGE)
    return key if key else None


def validate_config(exit_on_error: bool = False) -> bool:
    """Validate that mandatory runtime configurations are present.

    Args:
        exit_on_error: If True, prints error messages and terminates
            the process with exit code 1 instead of raising ValueError.

    Returns:
        bool: True if configuration is valid.

    Raises:
        ValueError: If required configuration is missing and exit_on_error is False.
        SystemExit: If required configuration is missing and exit_on_error is True.
    """
    try:
        get_api_key(required=True)
        return True
    except ValueError:
        if exit_on_error:
            print(ERROR_MESSAGE)
            raise SystemExit(1) from None
        raise


if __name__ == "__main__":
    validate_config(exit_on_error=True)
    print(f"Configuration valid. Base directory: {BASE_DIR}")
