# 🎯 Technical Interview Prep — AI Student Helper
*Detailed answers to technical and behavioral questions about the project, mapped directly to the codebase.*

---

## 🔷 SECTION 1: High-Level / Walkthrough

### 1. Tell me about your AI Student Helper — what problem does it solve and who's it for?
* **What it is**: **AI Student Helper** (also referred to as **I Student Helper**) is a premium, responsive, full-stack AI homework helper and study companion web application. It shares its backend database and core logic with a cross-platform Flutter mobile application.
* **The Problem**: Private tutoring is expensive and inaccessible to many, while search engines return millions of cluttered pages instead of a direct, simplified academic explanation. Additionally, standard LLM interfaces lack structured subject separation, late-night dark modes, and fail to render mathematical equations beautifully for students.
* **Who it's for**: Middle school, high school, and college students studying academic subjects like **Math, Science, Computer Science, History, and English**. It acts as a 24/7 personal tutor that explains complex concepts in a simplified, step-by-step manner.

### 2. Walk me through the full request lifecycle: user asks a question → what happens step by step until they get an answer?
1. **User Action**: The student types a question in the chat box on the Dashboard, selects a subject, chooses an AI model (Groq or Gemini), and clicks "Get Help".
2. **Frontend Interception**: In [main.js](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/static/js/main.js), Vanilla JS intercepts the form submit, disables the Send button, and inserts a "Typing..." loading spinner to handle latency.
3. **AJAX POST**: JavaScript makes a `fetch()` POST request to the `/dashboard` route in [app.py](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L687).
4. **Decorator Guard**: Flask executes the custom [login_required](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L197) decorator, verifying the user's session cookie is valid and the user still exists in the PostgreSQL database.
5. **Memory Retrieval**: The backend calls [get_session_active_chat](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L162) to retrieve the last 10 messages from PostgreSQL to construct the conversation context window (the AI's memory).
6. **Threaded Execution**: Inside the route, the backend spawns a Python daemon thread ([threading.Thread](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L723)) to execute `ask_ai` asynchronously. The main route waits up to 60 seconds using `_t.join(timeout=60)` so that the single-threaded Flask server is not blocked.
7. **Model Inference & Fallback**: The helper function [ask_ai](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L284) prepends a strict system prompt and executes the primary model, **Groq Llama 3.1-8b-instant**. If the Groq API call fails, it automatically and silently falls back to **Google Gemini 2.5 Flash**.
8. **Database Commit**: Once the answer returns, the server creates a new [Message](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L79) record containing the `user_id`, a generated UUID `chat_id`, the `subject`, the `question`, the `answer`, and the `model_used`, committing it to the PostgreSQL database.
9. **JSON Response**: Since the header indicates an AJAX call (`XMLHttpRequest`), the server returns a JSON payload: `{"question": ..., "answer": ..., "model": ..., "time": ...}`.
10. **UI Rendering**: JavaScript receives the JSON response, strips the typing indicator, appends a new message bubble to the screen, and calls **KaTeX** to render mathematical equations beautifully.

### 3. Why did you build this project? What gave you the idea?
* **Why**: I built this project to learn full-stack web and mobile development, API integration, OAuth 2.0 security, database relational modeling, and asynchronous task management. It is a showcase for recruiters of my ability to build clean, functional, secure software from scratch.
* **The Idea**: As a Computer Science student, I found myself getting stuck on advanced math and engineering concepts late at night when study centers were closed. I wanted a fast, responsive tutor tool that was built specifically for students, rendered clean mathematical equations, kept a organized history of my past study sessions, and was accessible on both my computer and phone.

---

## 🔷 SECTION 2: Backend & Architecture

### 4. Why Flask over Django or FastAPI?
* **Flask**: Lightweight, minimalist, and doesn't force a specific file structure. It gave me full control to design my own database connections (using SQLAlchemy) and manage user sessions, helping me learn how web components interact under the hood.
* **Django**: Far too heavy for this app. It forces its own rigid project layout, comes with built-in features (like a heavy Admin dashboard) that I didn't need, and abstracts away database/routing settings, which makes it harder to learn the core web foundations.
* **FastAPI**: While FastAPI is excellent for asynchronous REST APIs, it is not built with native Server-Side Template Rendering (SSR) in mind. Flask combines server-side Jinja2 template rendering (which makes loading the initial dashboard layout secure and fast) and API endpoints in a clean, unified project.

### 5. Why PostgreSQL over SQLite or MongoDB for this app?
* **PostgreSQL**: A robust, transactional relational SQL database. It is perfect for this app because our data is structured and relational (Users own Message histories in a clear 1-to-many relationship).
* **SQLite**: SQLite is a file-based database. Cloud platforms like Render use ephemeral filesystems. This means every time the server sleeps or restarts, a local `sqlite.db` file would be completely deleted, wiping all user accounts and history. PostgreSQL is hosted persistently in the cloud (on Neon Cloud), ensuring user data is safe across server lifecycles.
* **MongoDB**: MongoDB is a document-based (NoSQL) database. It does not enforce relational integrity, meaning it is harder to natively handle cascading deletes (e.g. deleting a user and automatically cleaning up their message history) or enforce foreign keys.

### 6. What does your database schema look like — what tables do you have and how are they related?
We have two main relational tables defined in [app.py](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L62-L93):
* **`User` Table**:
  * `id` (Integer, Primary Key)
  * `google_id` (String(255), Unique, Nullable)
  * `email` (String(255), Unique, Non-nullable)
  * `password` (String(255), Hashed, Nullable for Google logins)
  * `first_name` & `last_name` (String(255))
  * `default_subject` (String(100), defaults to "Math")
  * `settings` (JSON column to store flexible settings dictionary)
  * `session_token` (String(255), Unique, Nullable for mobile API authentication)
  * `created_at` (DateTime, defaults to UTC now)
* **`Message` Table**:
  * `id` (Integer, Primary Key)
  * `user_id` (Integer, Foreign Key pointing to `user.id`, Non-nullable)
  * `chat_id` (String(36), holds UUID of the conversation session)
  * `subject` (String(100))
  * `question` (Text, Non-nullable)
  * `answer` (Text, Non-nullable)
  * `model_used` (String(100))
  * `is_active` (Boolean, defaults to True)
  * `created_at` (DateTime, defaults to UTC now)
* **Relationship**: One user has many messages (`1-to-N`). It is defined using `messages = db.relationship('Message', backref='user', lazy=True)` in the `User` class.

### 7. How is chat history stored and retrieved per user?
* **Storage**: Every message exchange (one question and its answer) is saved as a single row in the `Message` table. A conversation thread is grouped by generating a unique `chat_id` (using `uuid.uuid4()`) when the chat begins.
* **Retrieval (History Page)**: In [get_session_history](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L128), SQLAlchemy fetches all messages for the user ordered by creation date descending. We loop through them, using a Python `seen_chat_ids` set to extract only the first message of each distinct conversation session. This lets us display preview cards on the history screen.
* **Retrieval (Active Chat)**: In [get_session_active_chat](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L162), when a user clicks a history card or continues a chat, their `active_chat_id` is stored in the session cookie. SQLAlchemy queries the database for all messages matching that `chat_id` and orders them chronologically to show the full back-and-forth conversation.

### 8. How does your app handle a user with no internet connection or a slow request?
* **No Internet**: The frontend JavaScript `fetch()` wrapper catches network exceptions and updates the UI with a clean error bubble ("Unable to connect to the server. Please check your internet connection.") rather than breaking the UI.
* **Slow Requests (Background Threading)**: Talking to AI models takes time (up to 15-20 seconds for complex queries). If a user waits on a synchronous Flask server thread, it hangs. To address this, Flask spawns a background thread in the dashboard route ([app.py: L723](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L723)) using `threading.Thread` and waits for it with `_t.join(timeout=60)`. If it times out or fails, it catches the exception and returns a friendly error message, maintaining server responsiveness.

---

## 🔷 SECTION 3: Authentication

### 9. Walk me through how Google OAuth 2.0 works in your app, step by step.
1. **Redirection Initiated**: The user clicks "Sign in with Google". Flask-Dance redirects the browser to Google’s OAuth 2.0 authorization server.
2. **User Consent**: The user logs in securely on Google's login interface and approves access to their email and profile details.
3. **Authorization Code Redirect**: Google redirects the user back to my backend endpoint (`/after-login`) with a temporary authorization code.
4. **Token Exchange**: Behind the scenes, my Flask app uses its secure `GOOGLE_CLIENT_SECRET` to call Google’s Token Endpoint, exchanging the authorization code for an Access Token.
5. **User Profile Retrieval**: The backend uses this Access Token to call Google’s `/oauth2/v2/userinfo` endpoint.
6. **Local Account Sync**: Flask reads the user's Google ID, checks the database, registers them if they are new, maps their details, and saves their info in the session cookie.

### 10. What data do you get back from Google after a successful login, and what do you do with it?
We get a JSON payload from Google containing:
* `id`: The user's unique Google Identifier.
* `email`: Their Google email address.
* `name`: Their full display name.
* `picture`: A URL pointing to their Google profile picture.

**What we do with it**: We store these details in Flask's encrypted session cookie (`session["user"]`). We query our database to check if a user with that `google_id` or `email` already exists. If they are a new user, they are redirected to `/setup` to collect their first/last name and default study subject. If they are an existing user, they are redirected to `/dashboard`.

### 11. How do you keep a user logged in across sessions?
* **On Web**: Flask's signed cookie sessions. When a user logs in, we save their identifier in Flask's `session` cookie. Because this cookie is cryptographically signed with the backend's secret key, the user's browser stores it, and Flask automatically reads and validates it on every request.
* **On Mobile (Flutter)**: Flutter apps do not natively use web cookies. On mobile, we use token-based authentication. When a user registers or logs in, the backend generates a random UUID `session_token` and saves it in the `User` database record. The Flutter app stores this token locally using the `shared_preferences` library and sends it as a `Bearer token` in the HTTP `Authorization` header on every request.

### 12. What would happen if someone tried to fake a login request — what's actually protecting you there?
* **Cryptographic Signatures**: The Flask session cookie is signed using the server's private `SECRET_KEY` using HMAC. If someone tries to modify the cookie values (e.g. changing the logged-in email to another user's email), the cryptographic signature becomes invalid. Flask detects this on the next request and deletes the session.
* **Ghost Session Verification**: In the decorator `login_required` ([app.py: L207](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L207)), even if a cookie is technically valid, the server checks the database to verify the user record still exists. If it doesn't find the user (for example, if the DB was wiped), it calls `session.clear()` and logs them out immediately.
* **OAuth Security**: The OAuth flow uses server-to-server validation. A client cannot fake a Google login because Google’s token exchange code is only valid once and requires our secret key to verify. On mobile, the server verifies the Google ID token via Google's tokeninfo API (`oauth2.googleapis.com/tokeninfo`).

---

## 🔷 SECTION 4: AI Integration

### 13. Why Groq's Llama 3 as primary instead of just using Gemini or OpenAI?
* **Extreme Speed**: Groq uses Language Processing Units (LPUs) that deliver speeds of over 200+ tokens per second. It returns responses in 1-2 seconds, creating an instant chat experience that matches the fast pacing of a homework helper.
* **Cost Efficiency**: Groq's API is free/very low cost for developer tiers compared to OpenAI's GPT-4, making it highly feasible for a student portfolio project.
* **Right-Sized Model**: Llama 3.1-8b-instant is perfect for answering core academic questions. It is fast, lightweight, and doesn't require the overhead of a massive model like GPT-4.

### 14. Walk me through the fallback logic — what specifically triggers switching from Groq to Gemini?
In `app.py`, the fallback logic is written using Python’s short-circuit evaluation:
```python
answer = ask_groq(messages) or ask_gemini(messages)
```
1. Flask executes [ask_groq(messages)](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L220).
2. Inside `ask_groq`, the POST request to the API is wrapped in a `try/except` block. If the API returns a status code other than 200 (like a `429 Too Many Requests` or `503 Service Unavailable`) or times out, the code catches it and returns `None`.
3. Because the left side of the `or` operator is `None` (falsy), Python immediately triggers the right side: [ask_gemini(messages)](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L248).
4. The switch happens automatically and silently in less than a second; the student never sees an error.

### 15. What happens if BOTH AI providers fail or time out?
* If both Groq and Gemini APIs return `None` (meaning both are down or timed out), the fallback logic sets:
  ```python
  answer = "⚠️ AI is temporarily unavailable. Please try again in a moment."
  ```
* This message is cleanly returned to the UI. The application does not crash, and the user is politely informed of the temporary outage without showing raw code stack traces.

### 16. How do you handle a malicious or harmful prompt from a user?
* **System Prompt Constraints**: The model is bound by a strict system prompt ([app.py: L289-300](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L289)) instructing it: *"You are 'AI Student Helper'... Explain things simply, concisely... Do NOT explain deep backend tech stack implementation details... Keep all answers clean, brief, and student-focused."*
* **API Safety Filters**: Both the Groq Llama and Google Gemini APIs run their own robust safety evaluation filters on their servers. If a user asks a harmful, dangerous, or abusive question, the model responds with a standard refusal.

### 17. Are you doing anything to control cost per API call (token limits, caching, etc.)?
* **Context Limitation**: Instead of sending the user's entire message history (which increases token count and cost with every reply), we slice the chat history list to include only the **last 10 messages** (`chat_history[-10:]`).
* **Max Token Guard**: In the Groq request, we configure `"max_tokens": 4000` to prevent the AI model from generating excessively long, wasteful text replies that consume API quotas.

### 18. How do you format the prompt you send to the LLM — is there a system prompt, and what's in it?
* **Format**: We pass a structured list of dictionaries containing roles and contents.
  * System Message (contains the app identity and formatting rules).
  * Past turns (alternating `user` and `assistant` messages).
  * Current turn (in the format `"[Subject] Question"`).
* **System Prompt Content**: Defined in `system_content` ([app.py: L289](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L289)), it instructs the AI to identify as "AI Student Helper", solve questions simply and concisely, and output math equations using KaTeX delimiters (`\( ... \)` for inline math and `\[ ... \]` for display blocks).

---

## 🔷 SECTION 5: Security & Deployment

### 19. Where are your API keys and secrets stored — walk me through that specifically.
* **In Development**: They are saved locally in a `.env` file in the project root. The `python-dotenv` package loads them, and we access them using `os.getenv()`.
* **In Production**: The `.env` file is excluded from git commits using `.gitignore`. On **Render**, these variables are entered in the **Environment Variables** dashboard. Render securely injects them into the application's runtime container, meaning they are never exposed in the codebase.

### 20. What would happen if someone found your GitHub repo — could they see any secrets?
**No**. The `.gitignore` file ([.gitignore: L2](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/.gitignore#L2)) ensures that `.env` files are never tracked or committed to GitHub. An open-source visitor will see only the clean Python code, keeping our keys and credentials completely secure.

### 21. What is "keep-alive ping" for, and why did you need it on Render?
* **Why it was needed**: Render's free tier spins down (puts to sleep) web services after 15 minutes of inactivity. When a new user visits, they experience a "cold start" delay of 30 to 60 seconds.
* **What it does**: We have a simple `/ping` route ([app.py: L337](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L337)) that returns a JSON message. We can configure a free uptime monitoring tool (like UptimeRobot) to hit this endpoint every 10-14 minutes, keeping the Render container active and preventing cold starts.

### 22. How do you handle errors so the app doesn't crash or show a blank screen to a user?
* **Global Error Handlers**: `@app.errorhandler(404)` and `@app.errorhandler(500)` decorators catch unhandled errors. If a route throws an error, the handler checks if it was an AJAX/JSON request and returns a JSON error, or redirects a web user to the home screen with a flashed message.
* **Try/Except Guards**: Every route has try/except blocks to log errors on the server while returning a user-friendly page or fallback message.
* **Database Rollbacks**: Every database failure calls `db.session.rollback()` inside the `except` blocks ([app.py: L462](file:///Users/mohammad/Downloads/Resume%20site/I%20Student%20Helper%20%E2%80%94%20Project/app.py#L462)), keeping the database session from getting stuck in an unusable, corrupted state.

---

## 🔷 SECTION 6: Scale, Users & Impact

### 23. You mentioned 10-20 active users and 99+ questions answered — how do you actually track and verify those numbers?
We verify these numbers directly from our PostgreSQL database:
* **Active Users Count**: Checked by running a query to count the total rows in the `User` table (`User.query.count()`).
* **Questions Answered Count**: Checked by running a query to count the total rows in the `Message` table (`Message.query.count()`).

### 24. If this had to scale to 10,000 users tomorrow, what would break first?
1. **Database Connection Pool**: PostgreSQL on Neon's free tier has a low limit of concurrent connections. 10k users would exhaust the connection pool instantly, throwing database errors.
2. **Server Threading Limit**: Our current implementation spawns new OS threads inside the Python runtime to call the AI. At scale, this would lead to high CPU context-switching overhead and memory leaks.
3. **API Rate Limits**: Groq and Gemini free API tiers would rate-limit us (429 status code) immediately, causing all users to receive fallback error messages.
* **How to fix**:
  * Implement connection pooling (e.g. PgBouncer) and upgrade database tiers.
  * Move to an asynchronous task queue like Celery and Redis to handle AI API calls asynchronously.
  * Add a cache (like Redis) for identical or highly similar questions to avoid querying the AI.
  * Move to paid API tiers with dedicated throughput.

### 25. What feedback did real users give you, and did it change anything about the app?
* **Feedback 1: Slow Responses**: Early testing showed students thought the app was frozen because calling AI takes 10+ seconds. This feedback led to creating the **Typing Spinner** and disabling the button on click.
* **Feedback 2: Reading Math Formulas**: Math students complained that raw equations were hard to parse. This led to configuring the system prompt for LaTeX equations and importing **KaTeX** on the frontend to render fractions, square roots, and matrices elegantly.
* **Feedback 3: Eye Strain**: Students studying late at night requested a dark theme. I implemented the **Dark Mode** toggle under Settings.

---

## 🔷 SECTION 7: Future / Extension

### 26. You're building a Flutter mobile app now — how are you exposing your existing Flask backend as an API for it?
Instead of rendering HTML, the Flutter app needs to communicate using JSON. We expose this in two ways:
1. **JSON Payload Interception**: The endpoints inside `app.py` check the headers:
   ```python
   if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
   ```
   If it is a JSON request, Flask returns a JSON response instead of a Jinja HTML template.
2. **Token Authentication**: To bypass session cookies, the backend generates a `session_token` for the user. The Flutter app saves this locally and sends it in the `Authorization` header (`Authorization: Bearer <token>`). The backend reads it to authenticate the user securely on every request.

### 27. If you added a new AI provider tomorrow, how much code would you need to change?
Very little, thanks to modular functions:
1. Add the new provider's API key to the `.env` file and Render settings.
2. Write a quick wrapper function in `app.py` (e.g. `ask_openai(messages)`), wrapped in try/except.
3. Add it to the short-circuit fallback chain inside `ask_ai()`:
   ```python
   answer = ask_groq(messages) or ask_openai(messages) or ask_gemini(messages)
   ```
The database structure, UI templates, and mobile API endpoints will remain completely untouched.
