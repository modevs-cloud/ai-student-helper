# AI Student Helper

**A full-stack web application that gives students instant AI-powered academic help on any subject.** 

Students can sign in with Google, ask questions across subjects, and receive clear step-by-step explanations — powered by Groq Llama 3 with Google Gemini as an automatic silent fallback. It's like having a personal tutor available 24/7.

[![Live Demo](https://img.shields.io/badge/Live-Demo-2ea44f?style=for-the-badge)](https://ai-student-helper-qsjg.onrender.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

---

## Features

- **Flexible Authentication:** Seamless Google OAuth 2.0 one-click sign-in plus Email & Password registration with Werkzeug salted password hashing (`pbkdf2:sha256`). After creating an account, users are sent to Sign In (email pre-filled) and then straight to the Dashboard's clean New Chat welcome screen.
- **Anti-Abuse Email Validation:** Signup accepts only permanent providers (Gmail, Outlook, Hotmail, Live, iCloud, Yahoo, Proton, AOL, Zoho, and school `.edu` / `.ac.*` domains). Temporary and disposable emails are blocked, including temporary-Google tricks (`+` aliases, `@googlemail.com`, and dot-permutation generator addresses). Validation runs both in the browser and on the server, and also applies to Google sign-in.
- **Duplicate Account Prevention:** Gmail addresses are canonicalized (dots ignored), so `john.doe@gmail.com` and `johndoe@gmail.com` cannot create two accounts. A duplicate signup is redirected to Sign In.
- **Privacy Policy Page:** Dedicated `/privacy` page linked from the signup form, footer, and settings.
- **Full Data Export:** Settings export includes the complete chat history with ISO-8601 timestamps.
- **Bring Your Own API Key (BYOK) Encrypted Vault:** Students can optionally connect their personal Anthropic Claude, Google Gemini, OpenAI, or Groq API keys in Settings — verified live against the provider, encrypted at rest in PostgreSQL (`PBKDF2-HMAC-SHA256` + `HMAC-SHA256`), and never exposed in browser cookies or DOM.
- **Interactive Dashboard & Hideable Hints:** A warm, distraction-free chat workspace that opens to a personalized New Chat welcome screen on every login, featuring pre-warmed Lottie thinking animations, pre-formatted DOM typewriter streaming (with zero raw Markdown asterisks shown while generating), KaTeX math rendering, syntax-highlighted code blocks, interactive hideable Hint cards (`Show hint` / `Hide hint`), and free scrolling while answers are generating.
- **Dual Built-in AI Models with Auto-Fallback:**
  - **Groq API with Llama 3** — the primary built-in model. Ultra-fast inference, great for quick answers.
  - **Google Gemini API** — automatic silent fallback. If Groq hits a rate limit or is unavailable, Gemini takes over instantly with no error shown to the user.
- **Smart Fallback Logic:** Groq is primary. If Groq fails for any reason, Gemini takes over automatically and silently — users never see an error.
- **Keep-Alive System:** Client-side ping every 10 minutes ensures the Render server never sleeps, so the app is always instant-on.
- **Chat History:** Grouped conversation sessions similar to ChatGPT, allowing students to revisit and continue past study sessions.
- **User Profiles:** Track questions asked and view subject breakdowns.
- **Customizable Settings:** Toggle between Dark and Light themes, set a default subject, and manage history.
- **Bulletproof Error Handling:** Global error handlers, per-route try/except guards, and database fallbacks ensure no user ever sees a raw Internal Server Error — every failure shows a clean, friendly message with automatic recovery.
- **Responsive Design:** Fully mobile-friendly UI that works seamlessly across all devices.

##  Tech Stack

**Frontend:**
- HTML5, CSS3, Vanilla JavaScript
- Jinja2 Templating

**Backend:**
- Python with Flask
- Flask-Session for state management

**Database:**
- PostgreSQL (hosted on Neon Cloud)
- Flask-SQLAlchemy

**Authentication:**
- Google OAuth 2.0 (Flask-Dance)

**AI Integrations:**
- Groq API (Llama 3) — primary model
- Google Gemini API — automatic silent fallback

**Deployment:**
- Hosted on Render using Gunicorn with automatic GitHub deploys

---

## Project Structure

```text
ai-student-helper/
├── app.py                  # Main Flask app, routes, BYOK vault, and database models
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn start command for Render
├── static/
│   ├── css/app-shell.css   # Unified warm dark/light design system & app shell
│   ├── css/style.css       # Legacy utility stylesheet
│   ├── js/main.js          # Frontend interactivity & keep-alive ping
│   └── thinking.lottie     # AI thinking indicator animation
└── templates/
    ├── base.html           # Public/onboarding layout (navbar, mobile drawer, footer)
    ├── app_base.html       # Authenticated workspace shell (collapsible sidebar, topbar)
    ├── _auth_styles.html   # Shared styles for Sign In, Sign Up, and Setup
    ├── landing.html        # Public homepage with live chat preview
    ├── signin.html         # Sign in page (Google OAuth + Email/Password)
    ├── signup.html         # Sign up page (Google OAuth + Email/Password)
    ├── setup.html          # Two-step onboarding setup (name & favorite subject)
    ├── dashboard.html      # Main AI chat interface
    ├── history.html        # Grouped conversation history with search & subject filter
    ├── profile.html        # User stats, subject breakdown, and account info
    ├── settings.html       # Learning preferences, BYOK API Keys vault, and theme
    ├── about.html          # About the project, models, and contact links
    └── privacy.html        # Privacy Policy & Terms of Use
```

## Database Architecture

The application uses a PostgreSQL database hosted on Neon Cloud, containing two main tables:

1. **User Table:** Stores Google ID, email, first and last name, default subjects, and join dates.
2. **Message Table:** Records every question and answer, tracking the subject, AI model used, chat session ID, and timestamps to seamlessly aggregate and restore conversations.

---

##  Running Locally

Follow these steps to run the application on your local machine.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/modevs-cloud/ai-student-helper.git
   cd ai-student-helper
   ```

2. **Set up the virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add the following variables:
   ```env
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgresql://your_neon_connection_string
   GROQ_API_KEY=your_groq_key
   GEMINI_API_KEY=your_gemini_key

   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   *Open your browser and navigate to `http://127.0.0.1:5001`*

---

##  Deploying to Render

1. Connect your GitHub repository to Render as a **Web Service**.
2. Set the build command to `pip install -r requirements.txt`.
3. Set the start command to `gunicorn app:app`.
4. Add all your environment variables in the Render dashboard.
5. In your Google Cloud Console, ensure your Render URL is added to the Authorized Redirect URIs: `https://your-app.onrender.com/login/google/authorized`.

---

## Built By

**Mohammad Hussainkhail**
- *Associate of Science in Computer Science — Community College of Aurora (2026)*
- *Currently pursuing BS in Computer Science at MSU Denver*
- **GitHub:** [@modevs-cloud](https://github.com/modevs-cloud)
- **Email:** [mohammadhu1058@gmail.com](mailto:mohammadhu1058@gmail.com)
