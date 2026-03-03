import requests
import json

url = "http://localhost:8000/api/v1/auth/register"
body = {
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
}

try:
    res = requests.post(url, json=body)
    print(f"Status: {res.status_code}")
    print(f"Headers: {res.headers}")
    print(f"Body: {res.text}")
except Exception as e:
    print(f"Error: {e}")
