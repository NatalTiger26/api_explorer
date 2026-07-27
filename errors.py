import requests


def handle_api_error(e):
  """Print a friendly message for a requests exception raised by call_model."""

  if isinstance(e, requests.exceptions.Timeout):
    print("\nThe request timed out.")
    print("The server may be busy. Please try again.")

  elif isinstance(e, requests.exceptions.ConnectionError):
    print("\nCould not connect to NVIDIA's servers.")
    print("Please check your internet connection.")

  elif isinstance(e, requests.exceptions.HTTPError):
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

  elif isinstance(e, requests.exceptions.RequestException):
    print("\nAn unexpected network error occurred.")
    print(f"API Error: {e}")