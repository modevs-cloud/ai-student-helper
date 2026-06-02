import os
import requests as req
from dotenv import load_dotenv

load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

print("GROQ KEY:", groq_key)
print("GEMINI KEY:", gemini_key)

print("\n--- Testing Groq ---")
resp = req.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
    json={
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Test"}],
        "max_tokens": 10,
    }
)
print("Groq Status:", resp.status_code)
print("Groq Response:", resp.text)

print("\n--- Testing Gemini ---")
resp = req.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_key}",
    json={"contents": [{"parts": [{"text": "Test"}]}]}
)
print("Gemini Status:", resp.status_code)
print("Gemini Response:", resp.text)
