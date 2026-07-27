import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("NVIDIA_API_KEY")

URL = "https://integrate.api.nvidia.com/v1/chat/completions"
print(Path.cwd())

BASE_DIR = Path(__file__).resolve().parent

CONVERSATION_DIR = Path("conversations")
CONVERSATION_FILE = CONVERSATION_DIR / "chat1.json"



def call_model(messages, model="meta/llama-3.1-8b-instruct", max_tokens=512):
  headers = {
      "Authorization": f"Bearer {API_KEY}",
      "Content-Type": "application/json"
  }

  # Can use the words json or payload interchangeably, but json is more common
  payload = {               
      "messages": messages,
      "model": model,    # Another model is nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
      "max_tokens": max_tokens,
    }


  response = requests.post(URL, headers=headers, json=payload)
  response.raise_for_status()

  data = response.json()

  # To be able to better understand the response you can use the following line to print the response in a more readable format
  # print(json.dumps(data, indent=4))

  return data['choices'][0]['message']['content']

def run_chat(messages):
  print("You can start chatting with the model. Type your message or type 'exit' to quit.")

  while True:
    # take an input from user input()
    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        print("Exiting and saving the chat.")
        # save_history(CONVERSATION_FILE, messages)
        break
    
    # add that input to messages list as a dictionary 
    messages.append({"role": "user", "content": user_input})
    # call the model with messages
    response = call_model(messages) 

    # add the response to the messages list as a dictionary
    messages.append({"role": "assistant", "content": response})

    print(f"Assistant: {response}")

  return messages

def load_history(path):
  # Load the file 
  if not path.exists():
    return [{"role": "system", "content": "You are a helpful assistant."}]

  with open(path, "r", encoding='utf-8') as f:
    #read the json object and return the messages list
    return json.load(f)

def save_history(path, messages):
  # open the file in write mode
  with open(path, "w", encoding='utf-8') as f:
  # save messages as a json object
    json.dump(messages, f, indent=2)  

if __name__ == "__main__":
  messages = load_history(CONVERSATION_FILE)
  messages = run_chat(messages)
  save_history(CONVERSATION_FILE, messages)
  print(f"Conversation was saved to {CONVERSATION_FILE}")

