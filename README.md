# 🎓 AI Student Helper

**A full-stack web application that gives students instant AI-powered academic help on any subject.** 

Students can sign in with Google, ask questions across subjects, and receive clear step-by-step explanations — powered by Groq Llama 3 with Google Gemini as an automatic silent fallback. It's like having a personal tutor available 24/7.

[![Live Demo](https://img.shields.io/badge/Live-Demo-2ea44f?style=for-the-badge)](https://ai-student-helper-qsjg.onrender.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

---

## ✨ Features

- **No Passwords Needed:** Seamless Google OAuth 2.0 integration for quick access.
- **Interactive Dashboard:** A chat-style interface where students ask questions on the left and receive AI answers on the right.
- **Dual AI Models with Auto-Fallback:**
  - **Groq API with Llama 3** — the primary model. Ultra-fast inference, great for quick answers.
  - **Google Gemini API** — automatic silent fallback. If Groq hits a rate limit or is unavailable, Gemini takes over instantly with no error shown to the user.
- **Smart Fallback Logic:** Groq is primary. If Groq fails for any reason, Gemini takes over automatically and silently — users never see an error.
- **Keep-Alive System:** Client-side ping every 10 minutes ensures the Render server never sleeps, so the app is always instant-on.
- **Chat History:** Grouped conversation sessions similar to ChatGPT, allowing students to revisit and continue past study sessions.
- **User Profiles:** Track questions asked and view subject breakdowns.
- **Customizable Settings:** Toggle between Dark and Light themes, set a default subject, and manage history.
- **Bulletproof Error Handling:** Global error handlers, per-route try/except guards, and database fallbacks ensure no user ever sees a raw Internal Server Error — every failure shows a clean, friendly message with automatic recovery.
- **Responsive Design:** Fully mobile-friendly UI that works seamlessly across all devices.

## 🛠️ Tech Stack

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

## 📂 Project Structure

```text
ai-student-helper/
├── app.py                  # Main Flask app, routes, and database models
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn start command for Render
├── static/
│   ├── css/style.css       # Custom styling and theming
│   └── js/main.js          # Frontend interactivity
└── templates/
    ├── base.html           # Master layout (navbar, footer)
    ├── landing.html        # Public homepage
    ├── signin.html         # Sign in page
    ├── signup.html         # Sign up page
    ├── setup.html          # First time name setup
    ├── dashboard.html      # Main AI chat interface
    ├── history.html        # Grouped conversation history
    ├── profile.html        # User stats and account info
    ├── settings.html       # Preferences and theme
    └── about.html          # About the project
```

## 🗄️ Database Architecture

The application uses a PostgreSQL database hosted on Neon Cloud, containing two main tables:

1. **User Table:** Stores Google ID, email, first and last name, default subjects, and join dates.
2. **Message Table:** Records every question and answer, tracking the subject, AI model used, chat session ID, and timestamps to seamlessly aggregate and restore conversations.

---

## 🚀 Running Locally

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
   # Optional fallback models
   KIMI_API_KEY=your_kimi_key
   NVIDIA_API_KEY=your_nvidia_key
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   *Open your browser and navigate to `http://127.0.0.1:5001`*

---

## ☁️ Deploying to Render

1. Connect your GitHub repository to Render as a **Web Service**.
2. Set the build command to `pip install -r requirements.txt`.
3. Set the start command to `gunicorn app:app`.
4. Add all your environment variables in the Render dashboard.
5. In your Google Cloud Console, ensure your Render URL is added to the Authorized Redirect URIs: `https://your-app.onrender.com/login/google/authorized`.

---

## 👨‍💻 Built By

**Mohammad Hussainkhail**
- *Associate of Science in Computer Science — Community College of Aurora (2026)*
- *Currently pursuing BS in Computer Science at MSU Denver*
- **GitHub:** [@modevs-cloud](https://github.com/modevs-cloud)
- **Email:** [24kdev02@gmail.com](mailto:24kdev02@gmail.com)