import os
from dotenv import load_dotenv
load_dotenv()
from app import ask_gemini, ask_groq

messages = [{"role": "user", "content": "What is 2+2?"}]
print("Gemini:", ask_gemini(messages))
print("Groq:", ask_groq(messages))
