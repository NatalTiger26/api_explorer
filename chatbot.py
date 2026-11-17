"""Interactive command-line chatbot entry point for API Explorer.

Wires together terminal I/O, session history loading and persistence,
NVIDIA API completions, and graceful error recovery.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import requests

from config import CONVERSATION_FILE, validate_config
from errors import handle_api_error
from history import load_history, save_history
from llm import call_model


def run_chat(
    messages: list[dict[str, str]],
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., None] = print,
    session: requests.Session | None = None,
) -> list[dict[str, str]]:
    """Run the interactive conversation loop with the user.

    Processes user input, calls the LLM, handles network failures with
    automatic message rollback, and yields an updated history.

    Args:
        messages: Ongoing conversation history containing system, user,
            and assistant messages.
        input_fn: Callable used to retrieve input from the user (defaults to built-in input).
        print_fn: Callable used to print output messages (defaults to built-in print).
        session: Optional HTTP session for connection reuse across turns.

    Returns:
        The updated messages list containing new user and assistant exchanges.
    """
    print_fn("You can start chatting with the model. Type your message or type 'exit' to quit.")

    while True:
        try:
            raw_input = input_fn("You: ")
        except (EOFError, KeyboardInterrupt):
            print_fn("\nExiting and saving the chat.")
            break

        user_input = raw_input.strip()

        if not user_input:
            print_fn("Please type a message before pressing Enter.")
            continue

        if user_input.lower() in ("exit", "quit"):
            print_fn("Exiting and saving the chat.")
            break

        # Append user message to memory
        messages.append({"role": "user", "content": user_input})

        try:
            response = call_model(messages, session=session)
        except requests.exceptions.RequestException as e:
            handle_api_error(e)
            # Roll back dangling user message on network failure
            if messages and messages[-1].get("role") == "user":
                messages.pop()
            continue
        except Exception as e:
            print_fn(f"\nAn error occurred while communicating with the model: {e}")
            if messages and messages[-1].get("role") == "user":
                messages.pop()
            continue

        messages.append({"role": "assistant", "content": response})
        print_fn(f"Assistant: {response}")

    return messages


def main(conversation_file: Path | None = None) -> int:
    """Main program entry point for API Explorer CLI.

    Args:
        conversation_file: Optional explicit path for conversation history.
            Defaults to CONVERSATION_FILE from config.

    Returns:
        Exit code (0 for success).
    """
    target_file = conversation_file or CONVERSATION_FILE

    # Ensure required environment configuration exists before entering UI loop
    validate_config(exit_on_error=True)

    print("=" * 50)
    print("API Explorer")
    print("=" * 50)

    if target_file.exists():
        print("Loaded previous conversation.")
    else:
        print("Starting a new conversation.")
    print()

    messages = load_history(target_file)

    try:
        with requests.Session() as session:
            messages = run_chat(messages, session=session)
    except KeyboardInterrupt:
        print("\n\nChat interrupted.")
        print("Saving conversation before exiting...")
    finally:
        save_history(target_file, messages)
        print(f"Conversation was saved to {target_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
