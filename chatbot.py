import requests

from llm2 import call_model
from errors import handle_api_error
from history import load_history, save_history
from config import CONVERSATION_FILE


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

    except requests.exceptions.Timeout as e:
      handle_api_error(e)
      messages.pop()
      continue

    except requests.exceptions.ConnectionError as e:
      handle_api_error(e)
      messages.pop()
      continue

    except requests.exceptions.HTTPError as e:
      handle_api_error(e)
      messages.pop()
      continue

    except requests.exceptions.RequestException as e:
      handle_api_error(e)
      messages.pop()
      continue


    # add the response to the messages list as a dictionary
    messages.append({"role": "assistant", "content": response})
    print(f"Assistant: {response}")
  return messages


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