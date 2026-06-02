import os
from dotenv import load_dotenv
load_dotenv()

from app import ask_ai, app

with app.app_context():
    chat_history = [{"question": "hi", "answer": "hello"}]
    answer = ask_ai("test question", "Math", "gemini", chat_history=chat_history)
    print("ANSWER:", answer)
