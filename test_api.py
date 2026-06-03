"""
test_api.py — End-to-end API test for AI Student Helper
Tests: signup → ask AI → history → clear → delete account
"""
import os, subprocess, sys, time, uuid, requests

BASE_URL = "http://127.0.0.1:5001"

# ── Start local Flask server ──────────────────────────────────────────────────
print("▶ Starting Flask server...")
proc = subprocess.Popen(
    [sys.executable, "app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)
time.sleep(4)  # give it time to boot

PASS = "✅"
FAIL = "❌"

def check(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label}  {detail}")
        raise AssertionError(label)

TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASS  = "TestPass123!"
session_token = None
headers = {}

try:
    # ── 1. Signup ─────────────────────────────────────────────────────────────
    print("\n[1] POST /api/signup")
    r = requests.post(f"{BASE_URL}/api/signup", json={
        "first_name": "Test",
        "last_name": "User",
        "email": TEST_EMAIL,
        "password": TEST_PASS,
    }, timeout=10)
    print(f"    Status: {r.status_code}  Body: {r.text[:200]}")
    check("signup returns 200", r.status_code == 200)
    data = r.json()
    check("session_token in response", "session_token" in data)
    session_token = data["session_token"]
    headers = {"Authorization": f"Bearer {session_token}"}
    print(f"    Token: {session_token[:12]}...")

    # ── 2. GET /api/user ──────────────────────────────────────────────────────
    print("\n[2] GET /api/user")
    r = requests.get(f"{BASE_URL}/api/user", headers=headers, timeout=10)
    print(f"    Status: {r.status_code}  Body: {r.text[:200]}")
    check("user returns 200", r.status_code == 200)
    check("email matches", r.json().get("email") == TEST_EMAIL)

    # ── 3. POST /api/ask  (the critical AI test) ──────────────────────────────
    print("\n[3] POST /api/ask  — 'What is 2 plus 2?'  model=groq")
    r = requests.post(f"{BASE_URL}/api/ask", json={
        "question": "What is 2 plus 2?",
        "subject": "Math",
        "model": "groq",
        "chat_id": str(uuid.uuid4()),
    }, headers=headers, timeout=40)
    print(f"    Status: {r.status_code}  Body: {r.text[:300]}")
    check("/api/ask returns 200", r.status_code == 200)
    data = r.json()
    check("answer field present", "answer" in data)
    check("answer is non-empty", len(data.get("answer", "")) > 0)
    check("answer not an error", "⚠️" not in data.get("answer", ""))
    print(f"    Answer snippet: {data['answer'][:120]}")

    # ── 4. GET /api/settings ──────────────────────────────────────────────────
    print("\n[4] GET /api/settings")
    r = requests.get(f"{BASE_URL}/api/settings", headers=headers, timeout=10)
    print(f"    Status: {r.status_code}")
    check("settings returns 200", r.status_code == 200)

    # ── 5. POST /api/settings ─────────────────────────────────────────────────
    print("\n[5] POST /api/settings")
    r = requests.post(f"{BASE_URL}/api/settings", json={
        "default_subject": "Science",
        "is_dark_mode": True,
        "font_size_selection": 1,
    }, headers=headers, timeout=10)
    print(f"    Status: {r.status_code}")
    check("save settings returns 200", r.status_code == 200)

    # ── 6. GET /api/history ───────────────────────────────────────────────────
    print("\n[6] GET /api/history")
    r = requests.get(f"{BASE_URL}/api/history", headers=headers, timeout=10)
    print(f"    Status: {r.status_code}  Sessions: {len(r.json())}")
    check("history returns 200", r.status_code == 200)
    check("at least 1 session", len(r.json()) > 0)

    # ── 7. DELETE /api/history ────────────────────────────────────────────────
    print("\n[7] DELETE /api/history")
    r = requests.delete(f"{BASE_URL}/api/history", headers=headers, timeout=10)
    print(f"    Status: {r.status_code}")
    check("clear history returns 200", r.status_code == 200)

    # ── 8. DELETE /api/account ────────────────────────────────────────────────
    print("\n[8] DELETE /api/account  (cleanup)")
    r = requests.delete(f"{BASE_URL}/api/account", headers=headers, timeout=10)
    print(f"    Status: {r.status_code}")
    check("delete account returns 200", r.status_code == 200)

    print("\n🎉  ALL 8 TESTS PASSED — /api/ask returns real AI answers!\n")

except AssertionError as e:
    print(f"\n{FAIL} Test failed: {e}\n")
    sys.exit(1)
except Exception as e:
    print(f"\n{FAIL} Unexpected error: {e}\n")
    sys.exit(1)
finally:
    print("▶ Stopping Flask server...")
    proc.terminate()
    proc.wait()
    print("   Server stopped.")
