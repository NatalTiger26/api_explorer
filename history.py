import json


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