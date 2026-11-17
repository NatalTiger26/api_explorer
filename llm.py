"""LLM interface module for API Explorer.

Dispatches chat completion requests to NVIDIA's hosted endpoints,
manages payload serialization, and extracts generated responses.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any

import requests

from config import (
    API_KEY,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    URL,
)


def call_model(
    messages: Sequence[Mapping[str, Any]],
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: float = DEFAULT_TIMEOUT,
    api_key: str | None = None,
    api_url: str | None = None,
    session: requests.Session | None = None,
) -> str:
    """Send a list of messages to the NVIDIA chat completions endpoint.

    Args:
        messages: A sequence of message dictionaries, each containing
            at least 'role' and 'content' keys.
        model: The model identifier hosted on NVIDIA NIM.
        max_tokens: Maximum number of tokens to generate in the completion.
        timeout: HTTP request timeout in seconds.
        api_key: Optional explicit API key. If omitted, falls back to
            the environment variable or config default.
        api_url: Optional explicit endpoint URL.
        session: Optional requests.Session instance for connection pooling.

    Returns:
        The text content of the assistant's reply.

    Raises:
        ValueError: If the API key is missing or the response payload is not valid JSON.
        requests.exceptions.RequestException: If the network request fails or HTTP
            status code indicates an error (e.g. 401, 404, 500).
        KeyError: If the response JSON lacks expected keys ('choices', 'message', 'content').
    """
    active_key = api_key or os.environ.get("NVIDIA_API_KEY", "").strip() or API_KEY
    if not active_key:
        raise ValueError(
            "NVIDIA_API_KEY is required to call the model. Set it in .env or pass api_key directly."
        )

    endpoint = api_url or URL
    headers = {
        "Authorization": f"Bearer {active_key}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "messages": list(messages),
        "model": model,
        "max_tokens": max_tokens,
    }

    if session is not None:
        response = session.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
    else:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=timeout,
        )

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as err:
        raise ValueError(f"Failed to parse JSON response from API: {err}") from err

    if not isinstance(data, dict):
        raise ValueError(
            f"Unexpected API response format: expected JSON object, got {type(data).__name__}"
        )

    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        raise KeyError("API response is missing a non-empty 'choices' field.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict) or "message" not in first_choice:
        raise KeyError("API response choice is missing 'message' field.")

    message = first_choice["message"]
    if not isinstance(message, dict) or "content" not in message:
        raise KeyError("API response message is missing 'content' field.")

    content = message["content"]
    return str(content) if content is not None else ""
