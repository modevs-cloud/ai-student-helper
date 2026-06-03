AI Student Helper
A full stack web application that gives students instant AI-powered academic help on any subject. Students sign in with Google, ask any question, and get a clear explanation from one of five free AI models — like having a personal tutor available anytime.
Live Demo: https://ai-student-helper-qsjg.onrender.com

What It Does
Students use Google to sign in, once with their name, and are taken to a chat-like dashboard where the student can pose questions to academics that span different fields such as Math, Science, Computer Science, History and English. All of these conversations are stored in a personal history, and students can alternate between 5 AI models according to their needs.

Features
No password required to Google In. A chat-type dashboard, whose messages are displayed on the right and questions are answered on the left by AI. Options of five AI models such as Groq Llama 3, Google Gemini, Kimi, Mistral Large, and Gamma 2B. Fallback logic that will be activated automatically in case of a failure in the primary model, falling back to a back-up model. Debrief chat Group activities as in ChatGPT so that students can revisit and continue previous chats. A profile page with name, email, a total amount of the questions asked, and with subject breakage. A settings page which contains a dark and light theme option and clear history. Mobile-friendly full responsive eCommerce.

Tech Stack
Frontend: HTML5, CSS3, Vanilla JavaScript, Jinja2 templating
Backend: Python with Flask for routing and session management
Database: PostgreSQL on Neon Cloud using Flask-SQLAlchemy
Authentication: Google OAuth 2.0 using Flask-Dance
AI Models: Groq API (Llama 3), Google Gemini API, Kimi API, NVIDIA NIM API (Mistral Large and Gemma 2B)
Deployment: Gunicorn on Render with automatic GitHub deploys

Project Structure
ai-student-helper/
├── app.py                  # Main Flask app, routes, and database models
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn start command for Render
├── static/
│   ├── css/style.css       # All custom styling
│   └── js/main.js          # Frontend interactivity
└── templates/
    ├── base.html           # Master layout with navbar and footer
    ├── landing.html        # Public homepage
    ├── signin.html         # Sign in page
    ├── signup.html         # Sign up page
    ├── setup.html          # First time name setup
    ├── dashboard.html      # Main AI chat interface
    ├── history.html        # Grouped conversation history
    ├── profile.html        # User stats and account info
    ├── settings.html       # Preferences and theme
    └── about.html          # About the project

Database
On the PostgreSQL on the Neon Cloud, there are two tables.
The information held in the user table includes the Google ID, email, first name, last name, the default subject and the date of joining of each student.
Every question and answer, including the subject, AI model applied, chat session ID, and time are stored in the message table to allow conversations to be aggregated and restarted.

Running Locally
bashgit clone https://github.com/modevs-cloud/ai-student-helper.git
cd ai-student-helper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Create a .env file in the root folder with these variables:
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://your_neon_connection_string
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
Then run:
bashpython app.py
Open your browser at http://127.0.0.1:5000

Deploying to Render
Connect your GitHub repo to Render as a Web Service. Set the build command to pip install -r requirements.txt and the start command to gunicorn app:app. Add all your environment variables in the Render dashboard. In Google Cloud Console add your Render URL to the authorized redirect URIs as https://your-app.onrender.com/login/google/authorized.

Built By
Mohammad Hussainkhail
Associate of Science in Computer Science — Community College of Aurora (2026)
Currently pursuing BS in Computer Science at MSU Denver
GitHub: github.com/modevs-cloud
Email: mohammadhu1058@gmail.com