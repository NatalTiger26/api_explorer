# API Explorer

A lightweight command-line chatbot that talks to NVIDIA's hosted LLM endpoint (NVIDIA NIM / `integrate.api.nvidia.com`). It keeps conversation history across sessions, and fails gracefully when the network or the API misbehaves.

## Features

- Persistent conversation history — pick up a previous chat exactly where you left off, stored as JSON.
- Clear, human-readable error messages for every common failure mode (timeouts, connection issues, auth problems, rate limits, server errors).
- A failed request never corrupts your conversation — your unsent message is rolled back automatically so you can retry cleanly.
- Small, modular codebase split by responsibility, so each part is easy to read, test, and extend on its own.

## Project structure

```
api_explorer/
├── chatbot.py        # Entry point: the chat loop and program startup/shutdown
├── llm.py             # Talks to the NVIDIA API (call_model)
├── errors.py          # Turns network/API exceptions into friendly messages
├── history.py         # Loads and saves conversation history to disk
├── config.py          # Environment variables, API URL, file paths
├── conversations/      # Saved chat history (JSON), created at runtime
├── example.json       # Sample conversation file showing the expected format
├── requirements.txt
└── README.md
```

| File | Responsibility |
|---|---|
| `config.py` | Loads `.env`, validates the API key exists, defines the API URL and conversation file paths. |
| `llm.py` | Sends the message list to the NVIDIA chat completions endpoint and returns the model's reply. |
| `errors.py` | Maps `requests` exceptions to plain-English explanations (see [Error handling](#error-handling) below). |
| `history.py` | Reads/writes the conversation as a JSON list of `{"role": ..., "content": ...}` messages. |
| `chatbot.py` | Runs the interactive loop, wires the other modules together, and saves history on exit. |

## Requirements

- Python 3.9+
- An NVIDIA API key with access to the NIM chat completions endpoint

Install dependencies:

```bash
pip install -r requirements.txt
```

## Setup

1. Clone the repo and move into it:
   ```bash
   git clone <your-repo-url>
   cd api_explorer
   ```
2. Create a `.env` file in the project root:
   ```
   NVIDIA_API_KEY="nvapi-your-key-here"
   ```
   This file is git-ignored and should never be committed.
3. Install dependencies (ideally inside a virtual environment):
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Usage

Run the chatbot:

```bash
python chatbot.py
```

- Type a message and press Enter to chat.
- Type `exit` to end the session — your conversation is saved automatically.
- Pressing `Ctrl+C` also saves your conversation before quitting.

Conversation history is stored in `conversations/chat1.json` and reloaded automatically the next time you run the program, so the assistant remembers prior context between sessions.

## Error handling

Every request to the model goes through `call_model()` in `llm.py`, but the *interpretation* of failures lives in `errors.py`, in a single function: `handle_api_error(e)`. This keeps `chatbot.py`'s chat loop focused on conversation flow, while all "what went wrong and what should the user do" logic lives in one place.

`handle_api_error` inspects the type of exception raised by the `requests` library and prints a message tailored to it:

| Exception | Meaning | Message shown |
|---|---|---|
| `requests.exceptions.Timeout` | The request took too long (20s timeout) to get a response. | Suggests the server may be busy and to try again. |
| `requests.exceptions.ConnectionError` | The request never reached NVIDIA's servers at all. | Suggests checking your internet connection. |
| `requests.exceptions.HTTPError` | The server responded, but with an error status code. | See the status-code breakdown below. |
| `requests.exceptions.RequestException` | Any other network-related failure not covered above. | Generic network error message with the underlying exception text. |

For `HTTPError`, the status code is inspected further:

| Status | Likely cause | Message shown |
|---|---|---|
| `401` | Invalid or missing API key | "Authentication failed." |
| `403` | Account not verified / lacks access | "Access denied." |
| `404` | Model name or endpoint doesn't exist | "The requested model or endpoint could not be found." |
| `429` | Too many requests too quickly | "Rate limit reached." |
| `500+` | Problem on NVIDIA's end | "NVIDIA's servers are currently experiencing issues." |
| Anything else | Unclassified HTTP error | Prints the raw status code. |

**Why this matters for conversation integrity:** if any of these exceptions are raised, the chat loop in `chatbot.py` calls `messages.pop()` before continuing. This removes the user's just-sent message from the in-memory conversation, so a failed request never leaves a "dangling" user message with no assistant reply. The user can simply retry — the conversation stays consistent, and nothing broken gets written to disk.

## Saving format

Conversations are saved as a JSON list of message objects, e.g.:

```json
[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Hello!"},
  {"role": "assistant", "content": "Hi there! How can I help you today?"}
]
```

If the saved file is missing or corrupted, `history.py` starts a fresh conversation with a default system prompt rather than crashing.

<!-- ## Notes

- Never commit your `.env` file or real API key — see `.gitignore`.
- `conversations/*.json` files are personal chat logs and are git-ignored by default; `example.json` is kept as a reference for the expected format. -->