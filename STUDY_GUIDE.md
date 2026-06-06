# 🎓 AI Student Helper — Personal Study Guide

> This guide is written by your own AI assistant based on reading every file in your project. Use it to study and nail any interview question about this app.

---

## SECTION 1 — Project Overview

### What the App Does

AI Student Helper is a web application that gives students instant AI-powered answers to academic questions. A student signs in (with Google or an email/password), types a question, picks a subject, and gets a clear, simplified answer from an AI model — like having a tutor on demand. The app saves every conversation so students can review their chat history, and it supports five different AI models with automatic fallback if one stops working.

### Who It's For and Why It Was Built

It was built by Mohammad as a portfolio showcase project to demonstrate full-stack web development skills. It is designed for students who need quick, reliable homework help on subjects like Math, Science, Computer Science, History, and English — and it's completely free to use.

### How the Whole App Fits Together

Think of the app like a restaurant:

- **The Frontend (HTML/CSS/JS templates)** — This is the dining room. It's what the student sees and clicks on. It's made of HTML files that are dynamically filled in by the server.
- **The Backend (app.py with Flask)** — This is the kitchen. It receives orders (requests), processes them (runs Python logic), fetches answers from AI services, and sends back food (responses).
- **The Database (PostgreSQL on Neon Cloud)** — This is the pantry / record book. It permanently stores every user account and every question-answer pair so nothing is ever lost.
- **The AI Models (Groq, Gemini, Kimi, NVIDIA)** — These are specialist chefs called in remotely. The backend calls them via the internet, sends them the question, and they send back an answer.
- **Render (cloud hosting)** — This is the building where the restaurant operates. It keeps the app running 24/7 on the internet.

---

## SECTION 2 — `app.py` Explained Line by Line

This is the heart of the entire project. Everything lives here.

### The Imports (Lines 1–19)

Every `import` line loads a tool or library that the code will use later.

| Import | What it does |
|---|---|
| `os` | Lets Python read environment variables (like API keys) stored on the server |
| `json` | Lets Python convert Python objects to JSON text and back |
| `hashlib` | Used to create a fake ID for manual sign-up users using their email |
| `base64` | Used to convert image files into text strings so they can be sent to AI vision APIs |
| `uuid` | Generates random unique IDs — used for chat session IDs and session tokens |
| `requests as req` | Lets Python make HTTP requests to external APIs (Groq, Gemini, etc.) |
| `Flask, render_template, session, redirect, url_for, flash, request, jsonify, g` | Core Flask tools: render pages, manage sessions, redirect users, send JSON responses |
| `make_google_blueprint, google` | From Flask-Dance — handles the entire "Sign in with Google" flow |
| `load_dotenv` | Reads the `.env` file and loads the secrets into environment variables |
| `wraps` | A decorator helper — used when building the `login_required` guard |
| `datetime` | Used to record timestamps on messages |
| `SQLAlchemy` | Python library that talks to the database without writing raw SQL |
| `ProxyFix` | Fixes how Flask reads the user's real IP address when behind Render's proxy servers |
| `CORS` | Allows other origins (like a mobile app) to call this server's API endpoints |

### App Initialization (Lines 24–62)

```python
app = Flask(__name__)
```
This creates the Flask application. `__name__` tells Flask what directory to work from.

```python
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
```
When deployed on Render, requests pass through proxy servers first. This line tells Flask to trust the real protocol (HTTPS) and hostname from those proxies so redirects work correctly.

```python
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
```
Flask needs a secret key to encrypt and sign session cookies. If someone tries to tamper with their session cookie, Flask will detect it.

```python
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
```
This allows OAuth to work on `http://` locally. On the live site it uses `https://` automatically.

**Database Connection (Lines 52–62):**
```python
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
```
Neon Cloud (and older Heroku/Render) gives a URL that starts with `postgres://`, but the modern SQLAlchemy library requires `postgresql://`. This one-liner fixes that automatically.

The `pool_recycle: 280` and `pool_pre_ping: True` settings keep the database connection alive by recycling it every 280 seconds and testing it before use — important on cloud databases that close idle connections.

### The Database Models (Lines 78–101)

A **model** is a Python class that represents a table in the database. Each attribute is a column.

#### `User` Model (Lines 78–89)

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer (Primary Key) | The unique auto-incremented ID for every user |
| `google_id` | String | The unique ID from Google's system — links the user to their Google account |
| `email` | String (Unique) | The user's email address — also used as a unique identifier |
| `password` | String | Stores a password for users who sign up with email instead of Google |
| `first_name` | String | The student's first name, entered during setup |
| `last_name` | String | The student's last name |
| `default_subject` | String | The subject the student chose as their default (e.g., "Math") |
| `settings` | JSON | A JSON blob storing all settings: theme, font size, model preference, etc. |
| `session_token` | String (Unique) | A random token used to authenticate API requests |
| `created_at` | DateTime | When the account was created |
| `messages` | Relationship | A virtual link to all messages belonging to this user |

#### `Message` Model (Lines 91–101)

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer (Primary Key) | Unique ID for every message |
| `user_id` | Integer (Foreign Key) | Links this message to the user who asked it |
| `chat_id` | String (UUID) | Groups messages into conversations (like ChatGPT sessions) |
| `subject` | String | The subject tag the student selected (Math, Science, etc.) |
| `question` | Text | The full question the student typed |
| `answer` | Text | The full AI-generated response |
| `model_used` | String | Which AI model answered this question (groq, gemini, etc.) |
| `image_url` | String | Path to an uploaded image if the student attached one |
| `is_active` | Boolean | Whether this message belongs to the currently active chat session |
| `created_at` | DateTime | Timestamp of when the question was asked |

### Route-by-Route Breakdown

#### `GET /` — Landing Page (Line 535)
The home page. If the user is already logged in, they get bounced straight to `/dashboard`. If not, the beautiful landing page is shown with a "Sign in with Google" button.

#### `GET /after-login` — Google OAuth Callback (Line 542)
This is where Google redirects the user after they approve sign-in. It does several things:
1. Fetches the user's profile from Google (name, email, picture, ID).
2. Stores this in the Flask session.
3. Checks if this user already exists in the database.
4. If they do → load their settings and go to Dashboard.
5. If they don't → redirect to Setup so they can enter their name.

#### `GET/POST /setup` — First-Time Name Setup (Line 582)
Only shown once, ever — when a brand new user signs in for the first time. The student types their first and last name and picks a default subject. This information is saved to the database and never asked again.

#### `GET/POST /signin` — Email/Password Sign In (Line 625)
An alternative to Google login. Students with a manual account enter their email and password. If valid, a session is created and they go to the dashboard.

#### `GET/POST /signup` — Manual Account Creation (Line 668)
Lets students create an account with email and password directly. Creates a new User record in the database.

#### `GET/POST /dashboard` — Main Chat Interface (Line 732)
This is the most important route. On a `GET` request, it loads the dashboard and shows the current chat. On a `POST` request (when the student clicks "Ask"):
1. Reads the question, subject, and model from the form.
2. Runs `ask_ai()` in a background thread with a 60-second timeout.
3. Saves the question and answer to the database.
4. If the request came from JavaScript (AJAX), returns a JSON response.
5. If it's a normal form submission, re-renders the page with the answer.

#### `GET /history` — Conversation History (Line 910)
Loads all of the student's past chat sessions from the database (up to 100), grouped by `chat_id`, and displays them in a timeline view.

#### `GET/POST /profile` — User Profile Page (Line 923)
Shows the student's name, email, total questions asked, and a subject breakdown. Also allows the student to update their display name.

#### `GET/POST /settings` — Settings Page (Line 966)
Lets students change their default subject, preferred AI model, theme (dark/light), font size, and other preferences. Also has a "Clear History" button that deletes all messages from the database.

#### `GET /about` — About Page (Line 1021)
A simple informational page about the project and its creator. No login required — anyone can see it.

#### `GET /logout` — Logout (Line 1028)
Saves any pending session data to the database, then clears the Flask session cookie entirely. The user is redirected to the landing page.

### The `ask_ai()` Function (Lines 468–530)

This is the function that actually gets an answer from an AI model.

**Step 1 — Build the System Prompt:**
The first message in every conversation is a "system" message that tells the AI its role. It's told to be "AI Student Helper", to explain things simply, and to use proper math notation. This shapes how it answers every question.

**Step 2 — Add Chat History:**
Up to the last 10 turns of the conversation are included. This is what gives the AI "memory" — it can see what was said before and answer follow-up questions properly.

**Step 3 — Add the New Question:**
The current question (tagged with the subject like `[Math] What is a derivative?`) is added as the final message.

**Step 4 — The Fallback Chain:**
Depending on which model the student chose, it tries that model first. If it fails (returns `None`), it automatically tries the next one. For example, if the student chose Groq:
```
Groq → Gemma → NVIDIA Mistral → Gemini → Kimi
```
If all 5 fail, a friendly warning message is returned instead of crashing.

### How Sessions Work

A **session** in Flask is like a backpack that travels with each user. When a student signs in:
1. Flask stores their info (email, name, settings) in the session.
2. Flask encrypts and signs this data and stores it in a browser **cookie**.
3. Every time the student visits any page, Flask reads this cookie to know who they are.
4. The `@login_required` decorator on protected routes checks for this session — if it's missing, the student is sent back to the landing page.

---

## SECTION 3 — Database Explained

### What is PostgreSQL?

PostgreSQL (often called "Postgres") is a database system — think of it as a very powerful, structured spreadsheet that lives on a server. Instead of Excel cells, you have tables with rows and columns. It's designed to store millions of records reliably and quickly, and multiple people can access it at the same time without data getting corrupted.

### Why Neon Cloud?

Neon is a cloud service that hosts a PostgreSQL database for you, so you don't have to set up and maintain your own database server. It has a free tier which is perfect for a portfolio project. It provides a connection URL that you paste into your environment variables, and your app connects to it automatically.

### The `User` Table — Every Column Explained

| Column | Simple Explanation |
|---|---|
| `id` | A number that auto-increases. User 1, User 2, User 3... Every user gets a unique one. |
| `google_id` | The unique ID Google assigns to every account. Used to recognize returning users. |
| `email` | The student's email. Acts as the main way to identify and find a user. |
| `password` | Only used for manual sign-up. Stored as plain text (in a real production app, this would be hashed for security). |
| `first_name` | Entered during setup — used to say "Welcome, Mohammad!" on the dashboard. |
| `last_name` | Same as above. |
| `default_subject` | What subject gets pre-selected when they open the dashboard. |
| `settings` | Stores ALL preferences as a JSON dictionary: theme, model, font size, etc. |
| `session_token` | A random code used by API callers to prove who they are. |
| `created_at` | Records when the account was first made. |

### The `Message` Table — Every Column Explained

| Column | Simple Explanation |
|---|---|
| `id` | Auto-incrementing unique number for each message. |
| `user_id` | Points back to the user who asked this question (this is the foreign key). |
| `chat_id` | A random UUID that groups messages into one conversation. All messages in one session share the same `chat_id`. |
| `subject` | The academic subject tag the student selected. |
| `question` | The full text of what the student asked. |
| `answer` | The full text of what the AI responded with. |
| `model_used` | Which AI actually answered — could be "groq", "gemini", etc. |
| `image_url` | If the student uploaded a photo (e.g., a photo of their homework), the file path is saved here. |
| `is_active` | True = part of the current open chat. False = part of a past session in history. |
| `created_at` | Timestamp of when the question was asked. |

### What is a Foreign Key?

A foreign key is a column in one table that points to a row in another table, creating a link between them.

In our project: the `user_id` column in the `Message` table is a foreign key that points to the `id` column in the `User` table.

**Real example:** If Mohammad has `id = 5` in the User table, then every question he ever asks will have `user_id = 5` in the Message table. This is how the app knows "these messages belong to Mohammad and not someone else." When you ask for Mohammad's history, the code says: "Find all messages WHERE user_id = 5."

Without this foreign key, every message would be a loose, disconnected record and there would be no way to know whose question is whose.

### What is Flask-SQLAlchemy and Why Use It?

Flask-SQLAlchemy is a bridge between Python and the PostgreSQL database. Instead of writing raw SQL like:
```sql
SELECT * FROM message WHERE user_id = 5 ORDER BY created_at DESC;
```
You write Python like:
```python
Message.query.filter_by(user_id=5).order_by(Message.created_at.desc()).all()
```

This is called an **ORM (Object-Relational Mapper)**. It translates your Python objects into database operations automatically. It's safer (protects against SQL injection attacks), easier to read, and works across different database types without changing your code.

---

## SECTION 4 — Authentication Explained

### What is Google OAuth 2.0?

OAuth 2.0 is a secure system that lets your app say "let Google handle the login" without ever seeing the user's Google password. Think of it like a hotel key card system — you don't give the hotel your house key; instead they give you a temporary card that only works for your room.

### What is Flask-Dance?

Flask-Dance is a Python library that does all the complicated OAuth 2.0 work for you. Without it, you'd have to manually handle redirects, token exchanges, and session management. Flask-Dance wraps all of that into a single setup:
```python
google_bp = make_google_blueprint(
    client_id=...,
    client_secret=...,
    scope=["openid", "email", "profile"],
    redirect_to="after_login",
)
```
This one block configures the entire Google Sign-In flow.

### The Full Login Flow — Step by Step

1. **Student clicks "Sign in with Google"** on the landing page. The button links to `/login/google` which is a route created automatically by Flask-Dance.

2. **Flask-Dance redirects to Google.** The browser goes to `accounts.google.com` and shows the Google account picker. The student never left your domain in any risky way — Google just handles the password check itself.

3. **Google confirms the identity.** Once the student picks their account and approves, Google gives your app a special, short-lived **access token** and redirects the browser back to your app at `/login/google/authorized`.

4. **Flask-Dance receives the token** and stores it internally. Then it redirects to the `redirect_to="after_login"` route you specified.

5. **The `after_login` route runs.** Your code calls `google.get("/oauth2/v2/userinfo")` which uses the token to ask Google: "who is this person?" Google responds with their name, email, profile picture, and unique Google ID.

6. **Your code checks the database.** Does a user with this Google ID (or email) exist in your database?
   - **Yes** → Load their name and settings, go to dashboard.
   - **No** → This is a new user, go to `/setup` to collect their name.

7. **The Flask session is created.** The user's info is stored in an encrypted cookie in their browser. Every future page visit reads this cookie to know who the student is.

### What is a Session?

A session is temporary storage that Flask keeps per user. It works using an encrypted browser cookie. When you log in:
- Flask puts your info into a Python dictionary: `session["user"] = {"email": "...", "name": "..."}`
- Flask encrypts this dictionary using your `SECRET_KEY` and sends it as a cookie to the browser.
- Every time you visit a page, the browser sends this cookie back, Flask decrypts it, and now Flask knows who you are again.
- When you log out, `session.clear()` wipes this cookie.

### Why Google OAuth Instead of Username and Password?

- **Security:** Google handles all the hard security work (password hashing, 2FA, breach detection). You never store the student's password.
- **Convenience:** Students don't need to remember another password. One click and they're in.
- **Trust:** Users trust Google. They're already logged into Google on most devices.
- **Less maintenance:** You don't have to build password reset emails, account verification, or handle security vulnerabilities in your login system.

---

## SECTION 5 — AI Models Explained

### What is an API?

An API (Application Programming Interface) is a way for two different software programs to talk to each other. Think of it like a waiter at a restaurant. You (your app) tell the waiter (the API) your order (the question). The waiter goes to the kitchen (the AI model's servers) and comes back with your food (the answer). You never go into the kitchen yourself.

In our app, when a student asks a question, the backend sends an HTTP request to, say, `api.groq.com`, including the question and the API key. Groq's servers process it and send back the answer as JSON text.

### The Five AI Models

**1. Groq API (Llama 3.1-8b-instant) — The Default**
Groq is a company that runs AI models on special ultra-fast chips (LPUs). They run Meta's Llama 3 model, which is a large language model trained by Meta (the Facebook company). It's the default because it's extremely fast and free. In our code, the model string is `"llama-3.1-8b-instant"` — 8 billion parameters, designed for speed.

**2. Google Gemini (gemini-2.5-flash)**
Gemini is Google's own AI model. `gemini-2.5-flash` is a version optimized for speed and cost. It also supports image analysis (vision), so when a student uploads a homework photo, Gemini can read it and answer based on what's in the image.

**3. Kimi (Moonshot AI — moonshot-v1-8k)**
Kimi is made by a Chinese AI company called Moonshot AI. It's a multilingual model with a large context window. In our app, it uses the endpoint `api.moonshot.cn`. It's a backup option.

**4. NVIDIA NIM — Mistral Large**
NVIDIA's NIM platform lets you access large, powerful models hosted on NVIDIA's GPU infrastructure. The model `mistralai/mistral-large-3-675b-instruct-2512` is a very capable French-built AI model. It's one of the biggest and most capable models in our stack.

**5. NVIDIA NIM — Gemma 2B**
Gemma is Google's open-source smaller model (`google/gemma-2-2b-it`), also hosted through NVIDIA NIM. "2B" means 2 billion parameters — smaller and faster than the others, good as a last resort.

### The Fallback Logic

The fallback chain is one of the smartest parts of the app. If the student chooses Groq but Groq's API is having issues (rate limit, timeout, server error), instead of showing the student an error, the app quietly tries the next model.

Here's the actual chain for the default Groq model:
```
1st try: Groq (Llama 3)
2nd try: Gemma 2B via NVIDIA
3rd try: Mistral Large via NVIDIA
4th try: Google Gemini
5th try: Kimi
```

In code, this uses Python's `or` shortcut:
```python
answer = ask_groq(messages) or ask_gemma(messages) or ask_nvidia(messages) or ask_gemini(messages) or ask_kimi(messages)
```
Python evaluates left to right. `ask_groq()` returns `None` if it fails, and `None or something_else` moves to the next option automatically. This makes the app extremely reliable.

### What is an API Key and Why Store it in `.env`?

An API key is like a password that proves to an external service (Groq, Google, etc.) that you are who you say you are and that you have permission to use their service. They're also used to track usage and enforce rate limits.

**Why NOT put it in your code:**
```python
# NEVER DO THIS:
key = "gsk_abc123secretkey456"  # Pushed to GitHub → anyone can steal it!
```

**Why store it in `.env`:**
The `.env` file lives only on your computer (or Render's secure environment). It is listed in `.gitignore`, so it is **never pushed to GitHub**. In code, you read it safely with:
```python
key = os.getenv("GROQ_API_KEY")
```
If someone clones your GitHub repo, they get your code but NOT your keys. The app won't work for them, and your API accounts stay safe.

---

## SECTION 6 — Frontend Explained

### What is Jinja2 Templating?

Jinja2 is a templating engine built into Flask. It lets your HTML files contain Python-like logic and variables. Think of it like a form letter where you leave blanks to be filled in.

**Example from `dashboard.html`:**
```html
<h1>Welcome back, {{ name }}!</h1>
```
When Flask renders this, it replaces `{{ name }}` with the actual student's name from Python, like `"Welcome back, Mohammad!"`. 

You can also use Jinja2 for logic:
```html
{% if user %}
  <a href="/logout">Log out</a>
{% else %}
  <a href="/login">Sign in</a>
{% endif %}
```
This way, the navbar shows different links depending on whether the student is logged in.

### What Does `base.html` Do?

`base.html` is the master template that every other page inherits from. It contains the parts that appear on every single page: the `<head>` section with fonts and CSS, the sticky navigation bar at the top, and the mobile hamburger menu.

Other templates start with:
```html
{% extends "base.html" %}
{% block content %}
  ... page-specific content here ...
{% endblock %}
```
This means: "Start with everything in `base.html`, then inject my specific content into the `{% block content %}` section." Without this, you'd have to copy-paste the navbar into every single HTML file and update each one separately whenever you made a change.

### What Does the CSS File Do?

The CSS file (`static/css/style.css`) controls all the visual design. Key design choices:

- **Dark theme by default** — Black (`#0d0d0d`) background with dark card surfaces, giving a modern, premium feel.
- **Teal/green accent color** (`#2dd4bf`, `#4ade80`) — Used for buttons, active states, and highlights.
- **CSS custom properties (variables)** — Things like `--accent-color` and `--bg-color` are defined once and used everywhere, making theme switching (dark/light) easy.
- **Responsive layout using Flexbox and Grid** — Elements stack vertically on mobile and spread horizontally on desktop automatically.
- **Smooth transitions** — Buttons and links have `transition: all 0.15s` for subtle hover animations.

### What Does the JavaScript Do?

The JavaScript in `dashboard.html` handles the dynamic, interactive parts that HTML alone can't do:

1. **AJAX Form Submission** — When the student clicks "Ask", JavaScript intercepts the form submit, sends it via `fetch()` (a background HTTP request), and updates the chat bubbles on screen without reloading the entire page. This is what makes it feel like a real chat app.

2. **Typing Indicator** — While waiting for the AI response, three animated dots appear in a chat bubble. This is pure JavaScript — it creates and removes DOM elements.

3. **MathJax Rendering** — Math answers use special notation like `\( x^2 \)`. JavaScript loads the MathJax library which converts these into beautifully formatted equations automatically.

4. **Theme Toggle** — A dark/light mode switch stores the preference in the session and applies it by changing the `data-theme` attribute on the `<html>` element.

5. **Mobile Hamburger Menu** — On small screens, the navbar collapses. The hamburger button JavaScript shows/hides the mobile menu.

### What is Responsive Design?

Responsive design means the website looks good on any screen size — from a 27-inch monitor to a small phone screen. We achieved this with:

- **CSS media queries** — Rules that only apply when the screen is smaller than a certain width. For example: `@media (max-width: 768px) { .desktop-nav { display: none; } }` — this hides the desktop navbar on phones.
- **Flexbox and Grid** — These CSS layout systems naturally allow elements to wrap and resize based on available space.
- **The meta viewport tag** in `base.html` — `<meta name="viewport" content="width=device-width, initial-scale=1.0">` — This tells mobile browsers not to shrink the page and to match their pixel width to the design.

---

## SECTION 7 — Deployment Explained

### What Does "Deployment" Mean?

Deployment means taking your app from running on your personal computer (where only you can see it at `http://localhost:5000`) and putting it on a server somewhere on the internet so anyone in the world can access it at a real URL like `https://ai-student-helper-qsjg.onrender.com`.

### What is Render and Why Use It?

Render is a cloud hosting platform that runs your Python web application on their servers. You connect your GitHub repository, and Render watches for new commits. Every time you push code to GitHub, Render automatically downloads it and redeploys.

We chose Render because:
- It has a **free tier** that's great for portfolio projects.
- It connects to GitHub for **automatic deployments**.
- It supports **environment variables** through a dashboard (no `.env` file needed in production).
- It handles **HTTPS (SSL)** automatically — your app gets a secure `https://` URL for free.

### What is Gunicorn and Why Not Just Use `python app.py`?

When you run `python app.py` locally, Flask starts its own built-in development server. This server is designed for one developer. It handles one request at a time, is not optimized for performance, and is **not safe or stable enough for real users**.

**Gunicorn** (Green Unicorn) is a production-grade WSGI server. When Render runs your app, it runs it with:
```
gunicorn app:app
```
This means: "Use Gunicorn to serve the Flask app called `app` inside the file called `app.py`."

Gunicorn can handle multiple simultaneous users, manages worker processes, and is built to run 24/7 reliably in a server environment.

### What is the `Procfile`?

The `Procfile` is a plain text file with one line that tells Render exactly what command to run to start your app:

```
web: gunicorn app:app
```

Without it, Render wouldn't know how to start your application. `web:` means this is a web process that handles HTTP requests.

### Environment Variables on Render

In development, you store secrets in a `.env` file. On Render, you never upload a `.env` file. Instead, you go to the Render dashboard, navigate to your app's "Environment" section, and manually add each key-value pair (like `GROQ_API_KEY = your_key`). Render injects these into the server's environment when the app starts, and your code reads them with `os.getenv("GROQ_API_KEY")` — exactly the same as locally. Your secrets never appear in your GitHub code.

### Automatic Deploys — How GitHub Triggers Render

1. You write code on your computer and run `git push origin main`.
2. GitHub receives the new commit and updates the repository.
3. Render has a **webhook** registered with your GitHub repo. GitHub automatically notifies Render: "Hey, new code just came in!"
4. Render pulls the latest code, runs `pip install -r requirements.txt` to install any new dependencies, and then restarts the app using the `Procfile` command.
5. The new version of your app is live — usually within 1–3 minutes of your push.

---

## SECTION 8 — Common Interview Questions and Answers

**Q: Tell me about a project you built.**

> I built AI Student Helper — a full-stack web application that gives students instant AI-powered homework help. Students sign in with Google, type a question, choose a subject like Math or Science, and get a clear explanation from an AI model. The app keeps their full conversation history, supports five different AI models with automatic fallback, and lets students upload images of their homework. It's deployed live on Render with a PostgreSQL database on Neon Cloud.

---

**Q: What is your tech stack and why did you choose it?**

> My backend is Python with Flask — I chose Flask because it's lightweight, I know Python well, and it's perfect for small-to-medium web apps without the overhead of a heavier framework. My database is PostgreSQL hosted on Neon Cloud, accessed through Flask-SQLAlchemy so I can write Python instead of raw SQL. For authentication I used Google OAuth 2.0 with Flask-Dance — it's more secure than building my own login system. The AI is powered by Groq, Gemini, Kimi, and NVIDIA NIM — all free APIs. For deployment I used Render and Gunicorn, which gives me free hosting with automatic GitHub deploys.

---

**Q: How does authentication work in your app?**

> I use Google OAuth 2.0 via the Flask-Dance library. When a student clicks "Sign in with Google", they're redirected to Google's login page. After they approve, Google sends my app an access token. I use that token to request the student's profile (name, email, ID) from Google's API. I then check if this Google ID exists in my database. If yes, I restore their session. If no, I create a new user record. The student's info is stored in an encrypted Flask session cookie that travels with every request. I also added a traditional email/password option for students who prefer not to use Google.

---

**Q: How do you store user data?**

> All user data is stored in a PostgreSQL database hosted on Neon Cloud. I have two tables. The `User` table stores the student's name, email, Google ID, preferences, and settings. The `Message` table stores every question and answer, along with the subject, which AI model was used, a chat session ID, and a timestamp. I use Flask-SQLAlchemy as an ORM, so I write Python code like `Message.query.filter_by(user_id=u.id).all()` instead of raw SQL.

---

**Q: What happens if one AI model fails?**

> I built a fallback chain. The app tries the student's chosen model first. If that returns `None` (meaning it timed out, hit a rate limit, or threw an error), Python's `or` operator automatically moves to the next model in the chain. For example, if Groq fails: it tries Gemma, then NVIDIA Mistral, then Gemini, then Kimi. All five would have to fail simultaneously for the student to see an error message. This makes the app much more reliable than depending on a single provider.

---

**Q: How did you deploy your app?**

> I deployed on Render. I connected my GitHub repository to Render's dashboard. Every time I push code to the main branch on GitHub, Render automatically detects the change via a webhook, pulls the new code, and redeploys the app. The `Procfile` tells Render to use Gunicorn to run the Flask app. All my API keys and secrets are stored as environment variables in Render's dashboard — never in my code. The database is on Neon Cloud and connects via a `DATABASE_URL` environment variable.

---

**Q: What was the hardest part of building this project?**

> The hardest part was getting the fallback AI chain to work reliably. Different AI providers have different API formats — Gemini uses a completely different JSON structure than Groq and NVIDIA. I had to write separate functions for each one and test them individually. I also ran into issues where the Render instance would run out of memory when the AI call took too long, causing "Worker was sent SIGKILL" errors. I solved this by wrapping the AI call in a Python thread with a 60-second timeout, so the server gracefully handles slow responses instead of crashing.

---

**Q: What would you improve if you had more time?**

> A few things: First, I'd properly hash passwords for users who sign up with email — right now they're stored as plain text which is a security risk. Second, I'd add streaming responses so the AI answer appears word-by-word like ChatGPT instead of all at once after a wait. Third, I'd add proper rate limiting to prevent abuse. Fourth, I'd add a study mode with flashcard generation and quiz features. Fifth, I'd set up proper logging and monitoring to get alerts when errors occur in production.

---

**Q: How does the frontend communicate with the backend?**

> There are two ways. First, traditional HTML forms: when a student submits a question, the browser sends a POST request to `/dashboard`. Flask processes it and returns a new rendered HTML page. Second, and more commonly, JavaScript's `fetch()` function for AJAX requests. When the student clicks "Ask", JavaScript intercepts the form submit, sends it as a background HTTP POST request with the header `X-Requested-With: XMLHttpRequest`, and Flask detects this and returns a JSON response instead of a full HTML page. JavaScript then takes that JSON and updates the chat bubbles on screen without a page reload, creating a smooth chat-like experience.

---

**Q: What is a REST API and does your app use one?**

> A REST API is a set of rules for how different software systems communicate over the web using standard HTTP methods. GET retrieves data, POST creates or sends data, DELETE removes data. My app has both a traditional web interface AND a REST API. The REST API endpoints start with `/api/` — for example `/api/ask` for asking questions and `/api/history` for getting past conversations. These endpoints return JSON instead of HTML and use a session token for authentication. I originally built these for an iOS companion app, though the project is now web-only.

---

**Q: What is a database and why did you use PostgreSQL?**

> A database is a structured system for storing and retrieving data persistently. Without it, all user data would disappear when the server restarts. I chose PostgreSQL because it's the industry standard relational database — it's powerful, reliable, open source, and free. It stores data in structured tables with rows and columns and enforces relationships between tables using foreign keys. Neon Cloud hosts it for free, which was perfect for this project. It's also the same database system used at companies like Instagram and Airbnb at scale.

---

**Q: How do you keep API keys secure?**

> API keys are stored in a `.env` file locally and as environment variables on Render's dashboard in production. The `.env` file is listed in `.gitignore`, so it is never committed to GitHub. In the Python code, I read them with `os.getenv("GROQ_API_KEY")` — the actual key value is never written directly in any code file. Even if someone finds my GitHub repository and reads all my code, they cannot use my APIs because they don't have the keys.

---

**Q: What is version control and how did you use GitHub?**

> Version control tracks every change made to your code over time, like a timeline of save points you can go back to. Git is the version control system, and GitHub is the cloud platform that stores the Git repository. Throughout this project, I committed code regularly with descriptive commit messages like "Fix Internal Server Error caused by NoneType strftime". Each commit is a snapshot. If I ever break something, I can revert to a previous commit. GitHub also connects to Render for automatic deployments — every `git push` triggers a redeploy.

---

**Q: What does Flask do in your project?**

> Flask is the web framework that runs the entire backend. It handles three main things: **routing** (deciding which Python function runs when a URL is visited), **templating** (filling in HTML files with real data using Jinja2), and **request/response handling** (reading form data, returning JSON, managing cookies and sessions). Every page in the app — landing, dashboard, history, profile, settings, about — is a Flask route defined in `app.py`.

---

**Q: How does the chat history work?**

> Every time a student asks a question, the question and the AI's answer are saved as a `Message` record in the database. Each message has a `chat_id` — a UUID that groups messages into one conversation session. When a student starts a new chat, a fresh `chat_id` is generated and all new messages get that ID. When they open History, the app queries the database for all their messages, groups them by `chat_id`, and displays them as separate conversation cards. Students can also click on any past chat to reload it into the dashboard and continue from where they left off.

---

## SECTION 9 — Glossary

| Term | Simple One-Sentence Definition |
|---|---|
| **Flask** | A Python library that makes it easy to build web apps by connecting URLs to Python functions. |
| **PostgreSQL** | A powerful, professional open-source database system that stores data in structured tables. |
| **SQLAlchemy** | A Python library that lets you interact with a database using Python code instead of SQL. |
| **OAuth** | A standard security protocol that lets users log in using a trusted third party (like Google) without sharing their password with your app. |
| **API** | A way for two software programs to talk to each other, usually by sending requests and receiving JSON data over the internet. |
| **API key** | A unique secret code that proves to an external service that you are authorized to use it. |
| **Session** | Temporary storage that remembers a logged-in user between page visits, stored as an encrypted cookie in their browser. |
| **Token** | A randomly generated string used as proof of identity, similar to a temporary password or badge. |
| **Route** | A URL path (like `/dashboard`) connected to a specific Python function that handles requests to that address. |
| **Endpoint** | Same as a route — a specific URL that your server responds to, often used in the context of APIs. |
| **Deployment** | The process of making your app available on the internet by running it on a cloud server. |
| **Gunicorn** | A production-grade Python web server that can handle multiple users simultaneously, unlike Flask's built-in development server. |
| **Render** | A cloud hosting platform that runs your web app on their servers and connects to GitHub for automatic deployments. |
| **Neon** | A cloud service that hosts a PostgreSQL database for free, providing a connection URL you use in your app. |
| **Jinja2** | A templating language built into Flask that lets you inject Python variables and logic directly into HTML files. |
| **CORS** | A browser security rule that controls which websites can make API requests to your server; you can configure it to allow specific origins. |
| **Environment variable** | A secret value (like an API key) stored on the server's operating system, not in your code, so it stays private. |
| **Git** | A version control system that tracks every change to your code files over time. |
| **GitHub** | A cloud platform that stores Git repositories and allows collaboration; also triggers automatic deployments on Render. |
| **Repository (repo)** | A folder tracked by Git containing all your project files and the full history of every change ever made. |
| **Commit** | A saved snapshot of your code at a specific moment in time, with a message describing what changed. |
| **Push** | Uploading your local Git commits to GitHub so others (and servers like Render) can see the latest code. |
| **Blueprint** | A Flask feature that lets you organize routes into separate files and register them onto the main app — used here for the API routes. |
| **Model** | In SQLAlchemy, a Python class that represents a table in the database; each instance represents one row. |
| **Migration** | The process of updating a database's structure (adding or removing columns/tables) without losing existing data. |
| **Foreign key** | A column in one database table that contains the ID of a row in another table, creating a link between them. |
| **JSON** | JavaScript Object Notation — a text format that looks like a Python dictionary, used to send data between the backend and frontend. |
| **HTTP** | The communication protocol used by browsers and servers to send requests and responses across the internet. |
| **GET** | An HTTP method used to retrieve data — visiting a webpage or loading a resource. Does not change any data. |
| **POST** | An HTTP method used to send data to the server — submitting a form, asking a question, or logging in. |
| **DELETE** | An HTTP method used to tell the server to remove a specific resource or piece of data. |

---

*Study Guide generated by Antigravity — based on full reading of all project files. Good luck with your interviews, Mohammad! 🎓*
