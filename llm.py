import requests

from config import API_KEY, URL


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