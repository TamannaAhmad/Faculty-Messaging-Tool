import requests
import json
import os

API_ID = os.environ['HYPERSENDER_ID']
API_TOKEN = os.environ['HYPERSENDER_API']
PHONE_NUMBER = os.environ['PHONE_NUMBER']
url = "https://app.hypersender.com/api/whatsapp/v1/"+API_ID+"/send-text-safe"

payload = json.dumps({
  "chatId": PHONE_NUMBER + "@c.us",
  "text": "okay",
  "link_preview": True
})
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': 'Bearer ' + API_TOKEN
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)