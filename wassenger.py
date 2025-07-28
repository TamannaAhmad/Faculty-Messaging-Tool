import requests
import os

API_KEY = os.environ["WASSENGER_API"]
PHONE_NUMBER = os.environ['PHONE_NUMBER']
url = "https://api.wassenger.com/v1/messages"

payload = {
    "phone": PHONE_NUMBER,
    "message": "Hello world! This is a test message."
}
headers = {
    "Content-Type": "application/json",
    "Token": API_KEY
}

try:
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    print("Message sent successfully.")
    print("Response:", response.json())  # Assuming the response is in JSON format
except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
except Exception as err:
    print(f"An error occurred: {err}")


