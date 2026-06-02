import os
import json
import hashlib
import base64
import uuid
import requests as req
from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# ─── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()

# ─── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    default_subject = db.Column(db.String(100), default="Math")
    settings = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='user', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.String(36), nullable=True)
    subject = db.Column(db.String(100))
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.String(100))
    image_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─── Uploads directory ────────────────────────────────────────────────────────
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

def save_uploaded_image(file_obj, user_id):
    """Save an uploaded image to disk and return its web-accessible URL path."""
    user_dir = os.path.join(UPLOADS_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    ext = os.path.splitext(file_obj.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(user_dir, filename)
    file_obj.save(filepath)
    return f"/static/uploads/{user_id}/{filename}"

# ─── Google OAuth blueprint ───────────────────────────────────────────────────
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_to="after_login",
)
app.register_blueprint(google_bp, url_prefix="/login")

SUBJECTS = ["Math", "Science", "Computer Science", "History", "English", "Other"]

# ─── Database Helpers ─────────────────────────────────────────────────────────

import hashlib

def make_mock_id(email):
    h = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    return str(int(h[:15], 16))

def get_user_record():
    if "user" not in session: 
        print("DEBUG: 'user' not in session")
        return None
    email = session["user"].get("email")
    print(f"DEBUG: get_user_record email={email}")
    if not email: return None
    u = User.query.filter_by(email=email).first()
    print(f"DEBUG: get_user_record user found={u is not None}")
    return u

def get_session_history():
    u = get_user_record()
    if not u: return []
    msgs = Message.query.filter_by(user_id=u.id).order_by(Message.created_at.desc()).all()
    
    chats = []
    seen_chat_ids = set()
    
    for m in msgs:
        c_id = m.chat_id
        if c_id:
            if c_id in seen_chat_ids:
                continue
            seen_chat_ids.add(c_id)
        
        chats.append({
            "id": m.id,
            "chat_id": m.chat_id,
            "subject": m.subject,
            "question": m.question,
            "answer": m.answer,
            "model": m.model_used.capitalize() if m.model_used else "Unknown",
            "time": m.created_at.strftime("%b %d, %Y %I:%M %p"),
            "image_url": m.image_url
        })
        
        if len(chats) >= 100:
            break
            
    return chats

def get_session_active_chat():
    u = get_user_record()
    if not u: return []
    
    active_chat_id = session.get("active_chat_id")
    if active_chat_id:
        msgs = Message.query.filter_by(user_id=u.id, chat_id=active_chat_id).order_by(Message.created_at.asc()).all()
        if not msgs:
            # Fallback
            msgs = Message.query.filter_by(user_id=u.id, is_active=True).order_by(Message.created_at.asc()).all()
    else:
        msgs = Message.query.filter_by(user_id=u.id, is_active=True).order_by(Message.created_at.asc()).all()
        
    return [{
        "id": m.id,
        "chat_id": m.chat_id,
        "subject": m.subject,
        "question": m.question,
        "answer": m.answer,
        "model": m.model_used.capitalize() if m.model_used else "Unknown",
        "time": m.created_at.strftime("%b %d, %Y %I:%M %p"),
        "image_url": m.image_url
    } for m in msgs]

# ─── Auth helpers ─────────────────────────────────────────────────────────────

def get_current_user():
    return session.get("user")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("landing"))
        
        # Verify user still exists in database (prevents ghost sessions after DB wipe)
        email = session["user"].get("email")
        if not email or not User.query.filter_by(email=email).first():
            session.clear()
            return redirect(url_for("landing"))
            
        return f(*args, **kwargs)
    return decorated_function


# ─── AI helper ────────────────────────────────────────────────────────────────

def ask_groq_vision(messages, image_b64, mime_type):
    """Call Groq vision model (llama-3.2-11b-vision-instruct) with an image."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    print(f"DEBUG: ask_groq_vision called. Key length: {len(key)}")
    if not key:
        return None
    # Build vision messages: inject image into the last user turn
    vision_messages = []
    for idx, msg in enumerate(messages):
        if msg["role"] == "user" and idx == len(messages) - 1:
            vision_messages.append({
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                    {"type": "text", "text": msg["content"]},
                ],
            })
        else:
            vision_messages.append(msg)
    try:
        resp = req.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.2-11b-vision-instruct",
                "messages": vision_messages,
                "max_tokens": 4000,
            },
            timeout=8,
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"Groq vision failed with status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Groq vision error: {e}")
    return None


def ask_gemini_vision(messages, image_b64, mime_type):
    """Call Gemini 1.5 Flash with an image using inlineData."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    print(f"DEBUG: ask_gemini_vision called. Key length: {len(key)}")
    if not key:
        return None
    # Convert messages to Gemini format; inject image into last user turn
    contents = []
    system_text = ""
    for idx, msg in enumerate(messages):
        if msg["role"] == "system":
            system_text = msg["content"]
        elif msg["role"] == "user":
            if idx == len(messages) - 1:  # Last user message gets the image
                parts = []
                if system_text:
                    parts.append({"text": system_text})
                    system_text = ""
                parts.append({"inline_data": {"mime_type": mime_type, "data": image_b64}})
                parts.append({"text": msg["content"]})
                contents.append({"role": "user", "parts": parts})
            else:
                text = (system_text + "\n\n" + msg["content"]) if system_text else msg["content"]
                contents.append({"role": "user", "parts": [{"text": text}]})
                system_text = ""
        elif msg["role"] == "assistant":
            contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
    try:
        resp = req.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
            json={"contents": contents},
            timeout=8,
        )
        if resp.ok:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            print(f"Gemini vision failed with status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Gemini vision error: {e}")
    return None


def ask_groq(messages):
    """Call Groq API (Llama 3) with a messages list. Returns answer string or None."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    print(f"DEBUG: ask_groq called. Key length: {len(key)}")
    if not key:
        return None
    try:
        resp = req.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": messages,
                "max_tokens": 4000,
            },
            timeout=8,
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"Groq API error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Groq error: {e}")
    return None


def ask_gemini(messages):
    """Call Gemini API with a messages list. Converts to Gemini multi-turn format."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    print(f"DEBUG: ask_gemini called. Key length: {len(key)}")
    if not key:
        return None
    try:
        # Convert OpenAI-style messages to Gemini contents format
        # System message becomes first user turn with special prefix
        contents = []
        system_text = ""
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            elif msg["role"] == "user":
                text = (system_text + "\n\n" + msg["content"]) if system_text else msg["content"]
                contents.append({"role": "user", "parts": [{"text": text}]})
                system_text = ""  # Only prepend once
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
        resp = req.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
            json={"contents": contents},
            timeout=8,
        )
        if resp.ok:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            print(f"Gemini API error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Gemini error: {e}")
    return None


def ask_kimi(messages):
    """Call Kimi (Moonshot AI) API with a messages list. Returns answer string or None."""
    key = os.getenv("KIMI_API_KEY", "").strip()
    if not key:
        return None
    try:
        resp = req.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "moonshot-v1-8k",
                "messages": messages,
                "max_tokens": 4000,
            },
            timeout=8,
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Kimi error: {e}")
    return None


def ask_nvidia(messages):
    """Call NVIDIA NIM API (Mistral Large) with a messages list. Returns answer string or None."""
    key = os.getenv("NVIDIA_API_KEY", "").strip()
    print(f"DEBUG: ask_nvidia called. Key length: {len(key)}")
    if not key:
        return None
    try:
        resp = req.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "mistralai/mistral-large-3-675b-instruct-2512",
                "messages": messages,
                "max_tokens": 4000,
                "temperature": 0.15,
                "top_p": 1.00,
                "stream": False,
            },
            timeout=8,
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"NVIDIA error: {e}")
    return None


def ask_gemma(messages):
    """Call Gemma (google/gemma-2-2b-it) via NVIDIA NIM API."""
    key = os.getenv("GEMMA_API_KEY", "").strip()
    if not key:
        return None
    try:
        resp = req.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "google/gemma-2-2b-it",
                "messages": messages,
                "max_tokens": 4000,
                "temperature": 0.15,
                "top_p": 1.00,
                "stream": False,
            },
            timeout=8,
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Gemma error: {e}")
    return None


def ask_ai(question, subject, model="groq", chat_history=None, image_b64=None, image_mime=None):
    """
    Ask the AI with the chosen model, passing full conversation history for memory.
    chat_history: list of dicts with 'question' and 'answer' keys (from active_chat session).
    image_b64: base64-encoded image bytes (optional).
    image_mime: MIME type of the image e.g. 'image/jpeg' (optional).
    """
    system_content = (
        "You are 'AI Student Helper' (also known as 'I Student Helper'), a premium AI-powered homework helper "
        "and study companion web application. Explain things simply, concisely, and clearly to the student. "
        "When answering math questions, use proper mathematical notation. For inline math use \\( ... \\) "
        "and for block/display equations use \\[ ... \\] so they render beautifully.\n"
        "Here is what you should know about this website:\n"
        "- Creator/Builder: This website was created and built by Mohammad as a helpful study companion project.\n"
        "- Purpose: To help students learn smarter and get instant, simplified explanations on academic subjects (Math, Science, History, English, CS).\n"
        "If a user asks who built this website or what it is, answer in a friendly, humble tone that it is "
        "an AI study companion created by Mohammad to help students learn. Do NOT explain deep backend tech stack implementation details, "
        "file databases, specific keys, or backend architecture. Keep all answers clean, brief, and student-focused."
    )

    # Build messages list with full conversation history for memory
    messages = [{"role": "system", "content": system_content}]

    # Add past conversation turns (up to last 10 to avoid token overflows)
    if chat_history:
        for item in chat_history[-10:]:
            messages.append({"role": "user", "content": item["question"]})
            messages.append({"role": "assistant", "content": item["answer"]})

    # Add the current question
    messages.append({
        "role": "user",
        "content": f"[{subject}] {question}"
    })

    if image_b64 and image_mime:
        # Route to vision-capable models first; fall back to text-only if they fail
        if model == "gemini":
            answer = (ask_gemini_vision(messages, image_b64, image_mime)
                      or ask_groq_vision(messages, image_b64, image_mime)
                      or ask_gemini(messages) or ask_groq(messages) or ask_nvidia(messages) or ask_gemma(messages))
        else:  # groq, kimi, nvidia, gemma, or any other — use groq/gemini vision
            answer = (ask_groq_vision(messages, image_b64, image_mime)
                      or ask_gemini_vision(messages, image_b64, image_mime)
                      or ask_groq(messages) or ask_gemini(messages) or ask_nvidia(messages) or ask_gemma(messages))
    else:
        if model == "gemini":
            answer = ask_gemini(messages) or ask_gemma(messages) or ask_nvidia(messages) or ask_groq(messages) or ask_kimi(messages)
        elif model == "kimi":
            answer = ask_kimi(messages) or ask_gemma(messages) or ask_nvidia(messages) or ask_groq(messages) or ask_gemini(messages)
        elif model == "nvidia":
            answer = ask_nvidia(messages) or ask_gemma(messages) or ask_groq(messages) or ask_gemini(messages) or ask_kimi(messages)
        elif model == "gemma":
            answer = ask_gemma(messages) or ask_nvidia(messages) or ask_groq(messages) or ask_gemini(messages) or ask_kimi(messages)
        else:  # groq (default)
            answer = ask_groq(messages) or ask_gemma(messages) or ask_nvidia(messages) or ask_gemini(messages) or ask_kimi(messages)

    if not answer:
        answer = (
            "⚠️ Could not get an AI answer. Please check that your API keys "
            "are correctly set in the .env file and restart the server."
        )
    return answer


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def landing():
    if get_current_user():
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/after-login")
def after_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Could not fetch your Google account info. Please try again.")
        return redirect(url_for("landing"))

    info = resp.json()
    google_id = str(info.get("id"))

    session["user"] = {
        "email":   info.get("email"),
        "name":    info.get("name"),
        "picture": info.get("picture"),
        "id":      google_id,
    }

    # ── Check if we have saved data for this user ─────────────────────────────
    saved = User.query.filter_by(google_id=google_id).first()
    if saved:
        # Returning user — restore their data, skip setup
        session["display_name"] = f"{saved.first_name} {saved.last_name}".strip()
        session["settings"]     = saved.settings or {"default_subject": saved.default_subject or "Math"}
        return redirect(url_for("dashboard"))
    else:
        # First time ever — go to setup
        return redirect(url_for("setup"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if "user" not in session:
        return redirect(url_for("landing"))
        
    if request.method == "POST":
        first   = request.form.get("first_name", "").strip()
        last    = request.form.get("last_name", "").strip()
        subject = request.form.get("default_subject", "Math")
        if first:
            display_name = f"{first} {last}".strip()
            session["display_name"] = display_name
            session["settings"] = {"default_subject": subject}
            # Persist so they never see this page again
            # create user in db since setup is for new google users
            new_user = User(
                google_id=session["user"]["id"],
                email=session["user"]["email"],
                first_name=first,
                last_name=last,
                default_subject=subject,
                settings={"default_subject": subject}
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("dashboard"))
    return render_template("setup.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    u_sess = get_current_user()
    if u_sess:
        if User.query.filter_by(email=u_sess.get("email")).first():
            return redirect(url_for("dashboard"))
        else:
            session.clear()
        
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Please enter both email and password.")
            return render_template("signin.html")
            
        # Find user
        user_record = User.query.filter_by(email=email).first()
        if not user_record:
            flash("No account found with this email.")
            return render_template("signin.html")
            
        if user_record.password != password:
            flash("Incorrect password. Please try again.")
            return render_template("signin.html")
            
        # Log in
        session["user"] = {
            "email": email,
            "name": f"{user_record.first_name} {user_record.last_name}".strip(),
            "picture": None,
            "id": user_record.google_id or make_mock_id(email)
        }
        session["display_name"] = session["user"]["name"]
        session["settings"] = user_record.settings or {"default_subject": user_record.default_subject or "Math"}
        
        flash("Welcome back! 👋")
        return redirect(url_for("dashboard"))
        
    return render_template("signin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    u_sess = get_current_user()
    if u_sess:
        if User.query.filter_by(email=u_sess.get("email")).first():
            return redirect(url_for("dashboard"))
        else:
            session.clear()
        
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip().lower()
        password   = request.form.get("password", "")
        confirm    = request.form.get("confirm_password", "")
        
        if not first_name or not email or not password:
            flash("Please fill in all required fields.")
            return render_template("signup.html")
            
        if password != confirm:
            flash("Passwords do not match. Please try again.")
            return render_template("signup.html")
            
        # Check if email already exists
        user_record = User.query.filter_by(email=email).first()
        if user_record:
            flash("An account with this email already exists.")
            return render_template("signup.html")
            
        # Generate mock id
        mock_id = make_mock_id(email)
        
        # Save credentials & info
        new_user = User(
            google_id=None, # null for manual signups
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            default_subject="Math",
            settings={"default_subject": "Math"}
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Create session
        session["user"] = {
            "email": email,
            "name": f"{first_name} {last_name}".strip(),
            "picture": None,
            "id": mock_id
        }
        session["display_name"] = session["user"]["name"]
        session["settings"] = {"default_subject": "Math"}
        
        flash("Account created successfully! Welcome! 🚀")
        return redirect(url_for("dashboard"))
        
    return render_template("signup.html")


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.args.get("clear"):
        u = get_user_record()
        if u:
            Message.query.filter_by(user_id=u.id).delete()
            db.session.commit()
        session.pop("active_chat_id", None)
        session.modified = True
        _persist_user()
        flash("All chat history cleared permanently! 🗑️")
        return redirect(url_for("dashboard"))

    if request.args.get("new_chat"):
        session.pop("active_chat_id", None)
        u = get_user_record()
        if u:
            Message.query.filter_by(user_id=u.id, is_active=True).update({"is_active": False})
            db.session.commit()
        session.modified = True
        _persist_user()
        flash("Started a new chat session! (Past questions saved in History tab) 🚀")
        return redirect(url_for("dashboard"))

    if request.args.get("save_chat"):
        flash("Chat session is already saved automatically to your history! 📁🚀")
        return redirect(url_for("dashboard"))

    # Load past chat from history index
    load_id = request.args.get("load_chat_id")
    if load_id:
        session["active_chat_id"] = load_id
        session.modified = True
        _persist_user()
        flash(f"Loaded past conversation from history! 📂")
        return redirect(url_for("dashboard"))

    user     = get_current_user()
    name     = session.get("display_name", user["name"].split()[0])
    settings = session.get("settings", {"default_subject": "Math"})
    answer   = None
    question = ""
    subject  = session.get("active_subject", settings.get("default_subject", "Math"))
    model    = session.get("active_model", settings.get("preferred_model", "groq"))
    error    = None

    is_new_answer = False

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        subject  = request.form.get("subject", "Math")
        model    = request.form.get("model", "groq")
        
        # Keep active selections synchronized in Flask-Session
        session["active_subject"] = subject
        session["active_model"] = model

        if not question:
            error = "Please type a question before clicking Get Help."
        else:
            # Handle optional image upload
            image_b64 = None
            image_mime = None
            image_url = None
            image_file = request.files.get("image")
            if image_file and image_file.filename:
                try:
                    image_bytes = image_file.read()
                    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                    image_mime = image_file.content_type or "image/jpeg"
                    # Save for display in chat
                    image_file.seek(0)
                    image_url = save_uploaded_image(image_file, session["user"]["id"])
                except Exception as e:
                    print(f"Image upload error: {e}")

            # Pass current active_chat as history so the AI has memory
            current_chat = get_session_active_chat()
            answer = ask_ai(question, subject, model,
                            chat_history=current_chat,
                            image_b64=image_b64, image_mime=image_mime)

            # Ensure we have an active chat ID
            if "active_chat_id" not in session:
                session["active_chat_id"] = str(uuid.uuid4())

            # Save to database
            u = get_user_record()
            if u:
                msg = Message(
                    user_id=u.id,
                    chat_id=session["active_chat_id"],
                    subject=subject,
                    question=question,
                    answer=answer,
                    model_used=model,
                    image_url=image_url,
                    is_active=True
                )
                db.session.add(msg)
                db.session.commit()
            session.modified = True

            # Persist updated history
            _persist_user()
            
            # Set flag for typewriter animation
            is_new_answer = True

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
            if error:
                from flask import jsonify
                return jsonify({"error": error}), 400
            
            time_str = "Just now"
            if u and 'msg' in locals():
                time_str = msg.created_at.strftime("%b %d, %Y %I:%M %p")
                
            from flask import jsonify
            return jsonify({
                "question": question,
                "answer": answer,
                "model": model.capitalize() if model else "Unknown",
                "time": time_str,
                "image_url": image_url
            })

    return render_template(
        "dashboard.html",
        user=user, name=name, subjects=SUBJECTS,
        answer=answer, question=question, subject=subject,
        model=model, error=error,
        default_subject=settings.get("default_subject", "Math"),
        groq_enabled=bool(os.getenv("GROQ_API_KEY", "").strip()),
        gemini_enabled=bool(os.getenv("GEMINI_API_KEY", "").strip()),
        kimi_enabled=bool(os.getenv("KIMI_API_KEY", "").strip()),
        nvidia_enabled=bool(os.getenv("NVIDIA_API_KEY", "").strip()),
        gemma_enabled=bool(os.getenv("GEMMA_API_KEY", "").strip()),
        chat_history=get_session_active_chat(),
        is_new_answer=is_new_answer,
    )


# ── History ───────────────────────────────────────────────────────────────────

@app.route("/history")
@login_required
def history():
    return render_template(
        "history.html",
        user=get_current_user(),
        name=session.get("display_name", ""),
        history=get_session_history(),
    )


# ── Profile ───────────────────────────────────────────────────────────────────

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = get_current_user()
    if request.method == "POST":
        full_name = request.form.get("first_name", "").strip()
        if full_name:
            session["display_name"] = full_name
            session.modified = True
            _persist_user()
            flash("Name updated successfully! 🎉")
            return redirect(url_for("profile"))
    return render_template(
        "profile.html",
        user=user,
        name=session.get("display_name", user["name"]),
        question_count=len(get_session_history()),
        history=get_session_history(),
        session=session,
    )


# ── Session Update ────────────────────────────────────────────────────────────

@app.route("/session_update", methods=["POST"])
@login_required
def session_update():
    data = request.get_json() or {}
    if "active_subject" in data:
        session["active_subject"] = data["active_subject"]
    if "active_model" in data:
        session["active_model"] = data["active_model"]
    if "theme" in data:
        settings = session.get("settings", {"default_subject": "Math"})
        settings["theme"] = data["theme"]
        session["settings"] = settings
    session.modified = True
    _persist_user()
    return jsonify({"status": "success"})


# ── Settings ──────────────────────────────────────────────────────────────────

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user     = get_current_user()
    settings = session.get("settings", {"default_subject": "Math"})

    if request.method == "POST":
        # Handle "Clear Chat History" button
        if request.form.get("clear_history"):
            u = get_user_record()
            if u:
                Message.query.filter_by(user_id=u.id).delete()
                db.session.commit()
                _persist_user()
                flash("History cleared! 🗑️")
        else:
            # Save all settings from the new form
            settings["default_subject"]  = request.form.get("default_subject", "Math")
            settings["preferred_model"]  = request.form.get("preferred_model", "groq")
            settings["theme"]            = "dark" if request.form.get("dark_mode") else "light"
            settings["compact_messages"] = bool(request.form.get("compact_messages"))
            settings["font_size"]        = request.form.get("font_size", "medium")
            settings["study_reminders"]  = bool(request.form.get("study_reminders"))
            settings["streak_alerts"]    = bool(request.form.get("streak_alerts"))
            settings["weekly_summary"]   = bool(request.form.get("weekly_summary"))
            settings["auto_save"]        = bool(request.form.get("auto_save"))
            settings["response_length"]  = request.form.get("response_length", "balanced")
            settings["show_timestamps"]  = bool(request.form.get("show_timestamps"))
            session["settings"] = settings
            
            # Sync active model/subject immediately
            session["active_subject"] = settings["default_subject"]
            session["active_model"]   = settings["preferred_model"]
            
            session.modified = True
            _persist_user()
            flash("Settings saved! ✅")
        return redirect(url_for("settings"))

    return render_template(
        "settings.html",
        user=user,
        name=session.get("display_name", user["name"]),
        subjects=SUBJECTS,
        settings=settings,
        groq_enabled=bool(os.getenv("GROQ_API_KEY", "").strip()),
        gemini_enabled=bool(os.getenv("GEMINI_API_KEY", "").strip()),
        kimi_enabled=bool(os.getenv("KIMI_API_KEY", "").strip()),
        nvidia_enabled=bool(os.getenv("NVIDIA_API_KEY", "").strip()),
        gemma_enabled=bool(os.getenv("GEMMA_API_KEY", "").strip()),
    )


# ── About ─────────────────────────────────────────────────────────────────────

@app.route("/about")
def about():
    return render_template("about.html", user=get_current_user())


# ── Logout ────────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    # Persist before clearing session
    _persist_user()
    session.clear()
    return redirect(url_for("landing"))


# ─── Helper: save current session to disk ────────────────────────────────────

def _persist_user():
    u = get_user_record()
    if u:
        u.settings = session.get("settings", {"default_subject": "Math"})
        display_name = session.get("display_name", "")
        if display_name:
            parts = display_name.split(" ", 1)
            u.first_name = parts[0]
            if len(parts) > 1:
                u.last_name = parts[1]
            else:
                u.last_name = ""
        db.session.commit()


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
