This application is for my resume to showcase my full-stack software engineering skills.

# AI Student Helper — Project Documentation

## What This App Does
AI Student Helper is a full-stack web application that gives students instant, step-by-step AI academic explanations across subjects (Math, Science, Computer Science, History, English, and Other). Students can sign in with Google OAuth 2.0 or register with a permanent email and password (`pbkdf2:sha256` hashed). The platform includes built-in AI models (Groq and Google Gemini with automatic model discovery, caching, and silent fallback) as well as a Bring Your Own Key (BYOK) encrypted API key vault supporting Anthropic Claude, Google Gemini, OpenAI, and Groq.

## Pages & User Flow
- **Landing Page (`/`)**: Public front page introducing the platform, interactive preview, and navigation to Sign In, Create Account, About, and Privacy Policy. Logged-in users are redirected directly to the Dashboard.
- **Sign Up (`/signup`) & Sign In (`/signin`)**: Supports one-click Google OAuth 2.0 and Email/Password authentication. Signup enforces permanent email providers (`gmail.com`, `outlook.com`, `hotmail.com`, `icloud.com`, `yahoo.com`, `proton.me`, `.edu`, etc.), blocks temporary/disposable emails and temporary Google alias/dot-permutation generators, prevents duplicate accounts (including canonicalized Gmail dot variations), and redirects newly registered users to Sign In (with email pre-filled) and then straight to the Dashboard.
- **Setup Page (`/setup`)**: First-time onboarding screen for Google OAuth sign-ins to confirm display name and default study subject.
- **Dashboard (`/dashboard`)**: The main interactive AI study workspace featuring:
  - Clean **New Chat welcome screen** on every login with personalized time-of-day greeting and recent chat cards.
  - Subject selector and AI model selector (Groq, Gemini, or student's custom BYOK model).
  - Pre-warmed Lottie + animated pulse thinking indicator that displays immediately on the first and every subsequent message on both desktop and mobile.
  - Pre-formatted DOM typewriter rendering (never displaying raw `*` or `**` Markdown markers while typing) with KaTeX math (`\(...\)` and `\[...\]`), syntax-highlighted IDE code blocks with one-click copy, collapsible **Show hint / Hide hint** cards, and non-blocking smart auto-scroll that allows students to freely scroll up and down while an explanation is generating.
- **History (`/history`)**: Displays past study conversations grouped by session (`chat_id`) with search, subject filtering, and one-click session restoration onto the Dashboard.
- **Profile (`/profile`)**: Shows student account details, total questions asked, subject distribution breakdown, and display name editing.
- **Settings (`/settings`)**:
  - **General & Learning Preferences**: Default subject, preferred AI model, academic grade level (Middle School, High School, College, Graduate), teaching style (Step-by-Step, Socratic, Direct, ELI5), response length, and optional practice problems.
  - **BYOK API Keys Vault**: Live provider verification (`/verify_api_key`) and per-user server-side encryption (`PBKDF2-HMAC-SHA256` + `HMAC-SHA256`) stored in PostgreSQL (`User.settings`) without ever exposing keys in browser cookies or DOM.
  - **Appearance & Data**: Dark/Light theme toggle, font size, compact mode, full JSON chat history export (`/export_data`) with ISO-8601 timestamps, and history clearing.
- **About (`/about`) & Privacy Policy (`/privacy`)**: Project overview, supported model catalog, creator contact information, and full data privacy/security documentation.

## Tech Stack
- **Frontend**: HTML5, CSS3 (`app-shell.css` and `style.css` unified warm dark/light theme), Vanilla JavaScript, Jinja2 templates, KaTeX, Highlight.js, DotLottie.
- **Backend**: Python, Flask, Gunicorn (`--workers 2 --threads 4 --timeout 120`).
- **Authentication & Security**: Google OAuth 2.0 (Flask-Dance), Werkzeug `pbkdf2:sha256` password hashing, per-user PBKDF2-SHA256 + HMAC-SHA256 API key encryption.
- **Database**: PostgreSQL hosted on Neon Cloud via Flask-SQLAlchemy (`User` and `Message` tables) with automatic connection pooling and retry resilience.
- **Deployment**: Hosted on Render with a client-side keep-alive ping (`/ping`) every 10 minutes.
