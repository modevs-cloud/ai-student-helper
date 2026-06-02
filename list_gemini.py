import os
import requests as req
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GEMINI_API_KEY", "").strip()

resp = req.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
if resp.ok:
    print([m['name'] for m in resp.json().get('models', [])])
else:
    print(f"Failed: {resp.status_code} - {resp.text}")
