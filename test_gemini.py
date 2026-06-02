import os
import requests as req
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GEMINI_API_KEY", "").strip()

models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-pro",
    "gemini-1.5-pro"
]

for m in models_to_test:
    resp = req.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}",
        json={
            "contents": [{"role": "user", "parts": [{"text": "hello"}]}]
        }
    )
    if resp.ok:
        print(f"{m}: OK")
    else:
        print(f"{m}: Failed - {resp.json().get('error', {}).get('message')}")
