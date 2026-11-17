"""Error handling module for API Explorer.

Transforms raw network, HTTP, and API exceptions into human-friendly messages
guiding the user on corrective actions without crashing the interactive session.
"""

from __future__ import annotations

import requests


def format_api_error(e: BaseException) -> str:
    """Format an exception into a user-friendly error message.

    Inspects requests-specific exceptions, HTTP status codes, and general errors
    to produce clear diagnostics.

    Args:
        e: The exception raised by the network call or model execution.

    Returns:
        A formatted, human-readable error string.
    """
    if isinstance(e, requests.exceptions.Timeout):
        return "\nThe request timed out.\nThe server may be busy. Please try again."

    if isinstance(e, requests.exceptions.ConnectionError):
        return "\nCould not connect to NVIDIA's servers.\nPlease check your internet connection."

    if isinstance(e, requests.exceptions.HTTPError):
        response: requests.Response | None = getattr(e, "response", None)
        status: int | None = (
            getattr(response, "status_code", None) if response is not None else None
        )

        if status == 401:
            return "\nAuthentication failed.\nYour API key may be invalid."
        if status == 403:
            return "\nAccess denied.\nCheck that your NVIDIA account is verified."
        if status == 404:
            return (
                "\nThe requested model or endpoint could not be found.\n"
                "Check the model name in your code."
            )
        if status == 429:
            return "\nRate limit reached.\nPlease wait a few moments before trying again."
        if status is not None and status >= 500:
            return "\nNVIDIA's servers are currently experiencing issues.\nPlease try again later."
        if status is not None:
            return f"\nHTTP Error ({status})"
        return "\nHTTP Error occurred with no response received."

    if isinstance(e, requests.exceptions.RequestException):
        return f"\nAn unexpected network error occurred.\nAPI Error: {e}"

    return f"\nAn unexpected error occurred: {e}"


def handle_api_error(e: BaseException) -> str:
    """Print a friendly message for a requests exception raised by call_model.

    Args:
        e: The exception raised during API communication.

    Returns:
        The formatted message that was printed to stdout.
    """
    message = format_api_error(e)
    print(message)
    return message
