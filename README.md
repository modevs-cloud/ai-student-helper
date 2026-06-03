# AI Student Helper 🎓

A full-stack web application that gives students instant AI-powered academic help on any subject. Students sign in with Google, ask any question, and get clear explanations from one of five free AI models — like having a personal tutor available on demand.

**Live Demo:** [https://ai-student-helper-qsjg.onrender.com](https://ai-student-helper-qsjg.onrender.com)

---

## 📖 What It Does

Students authenticate via Google Sign-in, enter their profile preferences once, and are taken to a chat-like dashboard. Here, students can ask academic questions spanning fields such as **Mathematics, Science, Computer Science, History, and English**. 

All conversations are stored in a personal history log, and students can dynamically switch between 5 different AI models to suit their learning needs.

---

## ✨ Features

*   **Google OAuth 2.0:** Secure login with one click (no passwords required).
*   **AI Chat Dashboard:** A clean user interface where responses are presented on the left and input controls sit on the right.
*   **Multi-Model Choice:** Alternate between 5 distinct models:
    *   *Groq Llama 3* (Fast & Free)
    *   *Google Gemini* (Advanced Reasoning)
    *   *Kimi* (Long Context)
    *   *Mistral Large* (Powerful & Precise)
    *   *Gemma 2B* (Code Generation)
*   **Automatic Fallback Routing:** If the primary choice (e.g., Groq) is rate-limited or offline, the app automatically fails over to a backup model (e.g., Gemini) to guarantee a continuous chat experience.
*   **Chat History Grouping:** Groups questions and answers into continuous threads (like ChatGPT) so students can revisit, review, and resume past study sessions.
*   **User Profiles & Metrics:** Shows your name, email, account age, and total questions asked with subject breakdowns.
*   **Custom Settings:** Configure default subjects, switch between light and dark themes, or clear your question history.
*   **Fully Responsive Mobile Design:** Beautifully optimized layout across mobile, tablet, and desktop screens.

---

## 🛠️ Tech Stack

*   **Frontend:** HTML5, CSS3 (Modern Dark Theme), Vanilla JavaScript, Jinja2 Templating
*   **Backend:** Python with Flask (Routing, Session management, and API handler)
*   **Database:** PostgreSQL hosted on **Neon Cloud** utilizing **Flask-SQLAlchemy**
*   **Authentication:** Google Sign-In via **Flask-Dance**
*   **AI Services:** Groq API (Llama 3), Google Gemini API, Kimi API, NVIDIA NIM API (Mistral Large & Gemma 2B)
*   **Deployment:** Gunicorn web server deployed on **Render** with automatic GitHub CD (Continuous Deployment)

---

## 🗄️ Database Design

The application connects to a remote PostgreSQL database on Neon Cloud and runs two primary tables:

### 1. `user`
Stores student accounts and preferences.
*   `id` (Primary Key)
*   `google_id` (Google OAuth unique ID)
*   `email` (Unique student email)
*   `first_name` & `last_name`
*   `default_subject` (Favorite subject preference)
*   `settings` (Theme & session configs)
*   `created_at` (Timestamp of sign-up)

### 2. `message`
Stores conversational entries and allows threads to be grouped and resumed.
*   `id` (Primary Key)
*   `user_id` (Foreign Key referencing `user.id`)
*   `chat_id` (UUID grouping the conversation thread)
*   `subject` (Math, Science, History, etc.)
*   `question` (User's query)
*   `answer` (AI-generated response)
*   `model_used` (Which AI responded)
*   `image_url` (Optional attached image path)
*   `created_at` (Timestamp of the message)

---

## 📂 Project Structure

```text
ai-student-helper/
├── app.py                  # Main Flask app, routes, and database models
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn start command for Render
├── static/
│   ├── css/
│   │   └── style.css       # Custom stylesheets (dark mode & layout)
│   └── js/
│       └── main.js         # AJAX request handling & UI interactivity
└── templates/
    ├── base.html           # Master layout with navbar and footer
    ├── landing.html        # Public welcome/home page
    ├── signin.html         # Login portal
    ├── signup.html         # Registration page
    ├── setup.html          # First-time profile setup
    ├── dashboard.html      # AI chat workspace
    ├── history.html        # Grouped history lists
    ├── profile.html        # User statistics and information
    ├── settings.html       # Theme and subject preferences
    └── about.html          # Resume portfolio background page
```

---

## 💻 Running Locally

### 1. Clone & Set Up Directory
```bash
git clone https://github.com/modevs-cloud/ai-student-helper.git
cd ai-student-helper
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup local Environment Variables
Create a `.env` file in the root folder with these variables:
```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://your_neon_connection_string
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
KIMI_API_KEY=your_kimi_key
NVIDIA_API_KEY=your_nvidia_key
GEMMA_API_KEY=your_gemma_key
```

### 4. Run the App
```bash
python app.py
```
Open your browser and navigate to **`http://127.0.0.1:5000`**

---

## 🚀 Deploying to Render

1. Connect your GitHub repository to Render as a new **Web Service**.
2. Set the configuration details as:
   *   **Language:** `Python`
   *   **Build Command:** `pip install -r requirements.txt`
   *   **Start Command:** `gunicorn app:app`
3. Add all your `.env` key-value pairs under the **Environment Variables** tab in Render.
4. Set up Google Console Redirect:
   *   In your **Google Cloud Console**, add your Render URL to your OAuth Authorized Redirect URIs:
       `https://your-app-name.onrender.com/login/google/authorized`

---

## 👨‍💻 Built By

**Mohammad Hussainkhail**
*   🎓 **Associate of Science in Computer Science** — *Community College of Aurora (2026)*
*   📖 **BS in Computer Science** — *MSU Denver (Currently pursuing)*
*   🐙 **GitHub:** [github.com/modevs-cloud](https://github.com/modevs-cloud)
*   📧 **Email:** [mohammadhu1058@gmail.com](mailto:mohammadhu1058@gmail.com)
