import os
import subprocess
import time
import requests
import sys

# Start the Flask app as a background process
print("Starting Flask application for testing...")
proc = subprocess.Popen(
    [sys.executable, "app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for the server to start
time.sleep(3)

BASE_URL = "http://127.0.0.1:5000"
session_token = None

try:
    # 1. Test unauthorized access
    print("\n[Test 1] GET /api/user without token...")
    r = requests.get(f"{BASE_URL}/api/user")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    assert r.status_code == 401
    print("Success: Unauthorized access blocked.")

    # 2. Test login with mock token
    print("\n[Test 2] POST /api/login with mock token...")
    login_payload = {"id_token": "mock_john"}
    r = requests.post(f"{BASE_URL}/api/login", json=login_payload)
    print(f"Status: {r.status_code}")
    res_data = r.json()
    print(f"Response: {res_data}")
    assert r.status_code == 200
    assert "session_token" in res_data
    session_token = res_data["session_token"]
    print(f"Success: Logged in. Token: {session_token}")

    headers = {"Authorization": f"Bearer {session_token}"}

    # 3. Test get user details
    print("\n[Test 3] GET /api/user with valid token...")
    r = requests.get(f"{BASE_URL}/api/user", headers=headers)
    print(f"Status: {r.status_code}")
    res_data = r.json()
    print(f"Response: {res_data}")
    assert r.status_code == 200
    assert res_data["email"] == "john@example.com"
    print("Success: User details retrieved successfully.")

    # 4. Test save settings
    print("\n[Test 4] POST /api/settings...")
    settings_payload = {
        "default_subject": "Computer Science",
        "compact_messages": True,
        "font_size": "large"
    }
    r = requests.post(f"{BASE_URL}/api/settings", json=settings_payload, headers=headers)
    print(f"Status: {r.status_code}")
    res_data = r.json()
    print(f"Response: {res_data}")
    assert r.status_code == 200
    assert res_data["default_subject"] == "Computer Science"
    assert res_data["settings"]["compact_messages"] is True
    print("Success: Settings updated successfully.")

    # 5. Test ask endpoint
    print("\n[Test 5] POST /api/ask...")
    ask_payload = {
        "question": "What is the capital of France?",
        "subject": "History",
        "model": "gemma",
        "chat_id": "test-chat-session-123"
    }
    r = requests.post(f"{BASE_URL}/api/ask", json=ask_payload, headers=headers)
    print(f"Status: {r.status_code}")
    res_data = r.json()
    print(f"Response (truncated answer): {res_data.get('question')} -> {res_data.get('answer')[:100]}...")
    assert r.status_code == 200
    assert "answer" in res_data
    print("Success: AI responded and answer was returned and saved.")

    # 6. Test history retrieval
    print("\n[Test 6] GET /api/history...")
    r = requests.get(f"{BASE_URL}/api/history", headers=headers)
    print(f"Status: {r.status_code}")
    res_data = r.json()
    print(f"Response: Number of sessions = {len(res_data)}")
    if len(res_data) > 0:
        print(f"First session subject: {res_data[0]['subject']}")
        print(f"First session messages: {len(res_data[0]['messages'])}")
    assert r.status_code == 200
    assert len(res_data) > 0
    print("Success: Chat history retrieved successfully.")

    # 7. Test clear history
    print("\n[Test 7] DELETE /api/history...")
    r = requests.delete(f"{BASE_URL}/api/history", headers=headers)
    print(f"Status: {r.status_code}")
    res_data = r.json()
    print(f"Response: {res_data}")
    assert r.status_code == 200

    # Verify history is now empty
    print("Verifying history is empty...")
    r = requests.get(f"{BASE_URL}/api/history", headers=headers)
    assert len(r.json()) == 0
    print("Success: All chat history cleared successfully.")

    print("\n🎉 ALL 7 API ENDPOINTS VERIFIED AND WORKING CORRECTLY! 🎉")

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    sys.exit(1)

finally:
    print("\nStopping Flask application...")
    proc.terminate()
    proc.wait()
    print("Server stopped.")
