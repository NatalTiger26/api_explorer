import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("NVIDIA_API_KEY")

if not API_KEY:
    print("\nERROR: NVIDIA_API_KEY was not found.")
    print("Create a .env file containing:")
    print('NVIDIA_API_KEY="nvapi-your-key-here"')
    print("or export the variable in your terminal.")
    raise SystemExit(1)

URL = "https://integrate.api.nvidia.com/v1/chat/completions"
print(Path.cwd())

BASE_DIR = Path(__file__).resolve().parent

CONVERSATION_DIR = Path("conversations")
CONVERSATION_FILE = CONVERSATION_DIR / "chat1.json"