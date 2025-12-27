import requests
import logging

logging.basicConfig(level=logging.DEBUG)

url = "http://127.0.0.1:8000/check-url"
data = {"url": "https://www.google.com""BN"}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")