import json
import os
from sys import exit
from pathlib import Path

import requests
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


  response = requests.post(URL, 
                           headers=headers, 
                           json=payload, 
                           timeout=20
                          )
  
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

    if not user_input:
      print("Please type a message before pressing Enter.")
      continue

    if user_input.lower() == "exit":
      print("Exiting and saving the chat.")
      # save_history(CONVERSATION_FILE, messages)
      break
    
    # add that input to messages list as a dictionary 
    messages.append({"role": "user", "content": user_input})
    # call the model with messages
    try:
      response = call_model(messages)

    except requests.exceptions.Timeout:
      print("\nThe request timed out.")
      print("The server may be busy. Please try again.")

      messages.pop()
      continue

    except requests.exceptions.ConnectionError:
      print("\nCould not connect to NVIDIA's servers.")
      print("Please check your internet connection.")

      messages.pop()
      continue

    except requests.exceptions.HTTPError as e:
      status = e.response.status_code

      if status == 401:
        print("\nAuthentication failed.")
        print("Your API key may be invalid.")
      elif status == 403:
        print("\nAccess denied.")
        print("Check that your NVIDIA account is verified.")
      elif status == 404:
        print("\nThe requested model or endpoint could not be found.")
        print("Check the model name in your code.")
      elif status == 429:
        print("\nRate limit reached.")
        print("Please wait a few moments before trying again.")
      elif status >= 500:
        print("\nNVIDIA's servers are currently experiencing issues.")
        print("Please try again later.")
      else:
        print(f"\nHTTP Error ({status})")

      messages.pop()
      continue

    except requests.exceptions.RequestException as e:
      print("\nAn unexpected network error occurred.")
      print(f"API Error: {e}")
      messages.pop()
      continue


    # add the response to the messages list as a dictionary
    messages.append({"role": "assistant", "content": response})
    print(f"Assistant: {response}")
  return messages

def load_history(path):
  # Load the file 
  if not path.exists():
    return [{"role": "system", "content": "You are a helpful assistant."}]

  try:
    with open(path,"r",encoding="utf-8") as f:
    #read the json object and return the messages list
      return json.load(f)
  except FileNotFoundError:
    return [{"role":"system","content":"You are a helpful assistant."}]
  except json.JSONDecodeError:
    print("Conversation file corrupted. Starting a new conversation.")
    return [{"role":"system","content":"You are a helpful assistant."}]

def save_history(path, messages):
  # open the file in write mode
  with open(path, "w", encoding='utf-8') as f:
  # save messages as a json object
    json.dump(messages, f, indent=2)  

if __name__ == "__main__":
  print("="*50)
  print("API Explorer")
  print("="*50)
  if CONVERSATION_FILE.exists():
    print("Loaded previous conversation.")
  else:
    print("Starting a new conversation.")
  print()

  messages = load_history(CONVERSATION_FILE)



  try:
    messages = run_chat(messages)
  except KeyboardInterrupt:
    print("\n\nChat interrupted.")
    print("Saving conversation before exiting...")
  finally:
    save_history(CONVERSATION_FILE, messages)
    print(f"Conversation was saved to {CONVERSATION_FILE}")

