import os
import uuid
import requests as req
from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify, g
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix


# ─── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()

# ─── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 280,
    "pool_pre_ping": True,
}
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()
    # Migration helper to add session_token column to user table if not present
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [c["name"] for c in inspector.get_columns("user")]
        if "session_token" not in columns:
            db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN session_token VARCHAR(255) UNIQUE;"))
            db.session.commit()
            print("Startup Migration: Added session_token column to user table.")
    except Exception as e:
        print(f"Startup Migration info/error: {e}")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    default_subject = db.Column(db.String(100), default="Math")
    settings = db.Column(db.JSON, nullable=True)
    session_token = db.Column(db.String(255), unique=True, nullable=True)
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
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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





def get_user_record():
    if "user" not in session: 
        return None
    email = session["user"].get("email")
    if not email: return None
    u = User.query.filter_by(email=email).first()
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
            "time": m.created_at.strftime("%b %d, %Y %I:%M %p") if m.created_at else "Just now"
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
        "time": m.created_at.strftime("%b %d, %Y %I:%M %p") if m.created_at else "Just now"
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


def ask_groq(messages):
    """Call Groq API (Llama 3) with a messages list. Returns answer string or None."""
    key = os.getenv("GROQ_API_KEY", "").strip()
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
            timeout=45,
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"Groq API error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"Groq error: {e}")
    return None


def ask_gemini(messages):
    """Call Gemini API with a messages list. Converts to Gemini multi-turn format."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    try:
        contents = []
        system_text = ""
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            elif msg["role"] == "user":
                text = (system_text + "\n\n" + msg["content"]) if system_text else msg["content"]
                contents.append({"role": "user", "parts": [{"text": text}]})
                system_text = ""
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
        resp = req.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
            json={"contents": contents},
            timeout=45,
        )
        if resp.ok:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            print(f"Gemini API error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"Gemini error: {e}")
    return None



def ask_ai(question, subject, model="groq", chat_history=None):
    """
    Ask the AI — Groq Llama 3 is the primary model, Gemini is the automatic silent fallback.
    If the chosen model fails for any reason, the other is tried automatically.
    chat_history: list of dicts with 'question' and 'answer' keys.
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

    # ── Route to models: Groq = primary, Gemini = silent automatic fallback ─────────
    if model == "gemini":
        # Gemini first, Groq as silent fallback
        answer = ask_gemini(messages) or ask_groq(messages)
    else:  # groq (default)
        # Groq first, Gemini as silent fallback
        answer = ask_groq(messages) or ask_gemini(messages)

    if not answer:
        answer = (
            "⚠️ AI is temporarily unavailable. Please try again in a moment."
        )
    return answer



# ─── Routes ────────────────────────────────────────────────────────────────────────

# ── Keep-alive ping (prevents Render free tier from sleeping) ───────────────

@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "AI Student Helper is alive"}), 200


@app.route("/")
def landing():
    try:
        if get_current_user():
            return redirect(url_for("dashboard"))
        return render_template("landing.html")
    except Exception as e:
        print(f"ERROR /landing: {e}")
        return render_template("landing.html")


@app.route("/after-login")
def after_login():
    try:
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
        try:
            saved = User.query.filter_by(google_id=google_id).first()
            if not saved and info.get("email"):
                email_clean = info.get("email").lower().strip()
                saved = User.query.filter_by(email=email_clean).first()
                if saved:
                    saved.google_id = google_id
                    db.session.commit()
        except Exception as db_err:
            print(f"ERROR after_login DB lookup: {db_err}")
            saved = None

        if saved:
            session["display_name"] = f"{saved.first_name} {saved.last_name}".strip()
            session["settings"]     = saved.settings or {"default_subject": saved.default_subject or "Math"}
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("setup"))
    except Exception as e:
        print(f"ERROR /after-login: {e}")
        flash("Something went wrong during sign-in. Please try again.")
        return redirect(url_for("landing"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    try:
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
                
                try:
                    email_clean = session["user"]["email"].lower().strip()
                    existing_user = User.query.filter_by(email=email_clean).first()
                    
                    if existing_user:
                        existing_user.google_id = session["user"]["id"]
                        existing_user.first_name = first
                        existing_user.last_name = last
                        existing_user.default_subject = subject
                        existing_user.settings = {"default_subject": subject}
                        db.session.commit()
                    else:
                        new_user = User(
                            google_id=session["user"]["id"],
                            email=email_clean,
                            first_name=first,
                            last_name=last,
                            default_subject=subject,
                            settings={"default_subject": subject}
                        )
                        db.session.add(new_user)
                        db.session.commit()
                except Exception as db_err:
                    print(f"ERROR /setup DB save: {db_err}")
                    db.session.rollback()
                    flash("Could not save your profile. Please try again.")
                    return render_template("setup.html")
                    
                return redirect(url_for("dashboard"))
        return render_template("setup.html")
    except Exception as e:
        print(f"ERROR /setup: {e}")
        return render_template("setup.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    try:
        u_sess = get_current_user()
        if u_sess:
            try:
                if User.query.filter_by(email=u_sess.get("email")).first():
                    return redirect(url_for("dashboard"))
                else:
                    session.clear()
            except Exception:
                session.clear()
            
        if request.method == "POST":
            email    = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            
            if not email or not password:
                flash("Please enter both email and password.")
                return render_template("signin.html")

            try:
                user_record = User.query.filter_by(email=email).first()
            except Exception as db_err:
                print(f"ERROR /signin DB: {db_err}")
                flash("Database temporarily unavailable. Please try again.")
                return render_template("signin.html")
                
            if not user_record:
                flash("No account found with this email.")
                return render_template("signin.html")
                
            if user_record.password != password:
                flash("Incorrect password. Please try again.")
                return render_template("signin.html")
                
            session["user"] = {
                "email": email,
                "name": f"{user_record.first_name} {user_record.last_name}".strip(),
                "picture": None,
                "id": user_record.google_id or str(uuid.uuid4())
            }
            session["display_name"] = session["user"]["name"]
            session["settings"] = user_record.settings or {"default_subject": user_record.default_subject or "Math"}
            
            flash("Welcome back! 👋")
            return redirect(url_for("dashboard"))
            
        return render_template("signin.html")
    except Exception as e:
        print(f"ERROR /signin: {e}")
        flash("Something went wrong. Please try again.")
        return render_template("signin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    try:
        u_sess = get_current_user()
        if u_sess:
            try:
                if User.query.filter_by(email=u_sess.get("email")).first():
                    return redirect(url_for("dashboard"))
                else:
                    session.clear()
            except Exception:
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

            try:
                user_record = User.query.filter_by(email=email).first()
                if user_record:
                    flash("An account with this email already exists.")
                    return render_template("signup.html")
                    
                mock_id = str(uuid.uuid4())
                new_user = User(
                    google_id=None,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    default_subject="Math",
                    settings={"default_subject": "Math"}
                )
                db.session.add(new_user)
                db.session.commit()
            except Exception as db_err:
                print(f"ERROR /signup DB: {db_err}")
                db.session.rollback()
                flash("Could not create your account. Please try again.")
                return render_template("signup.html")
            
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
    except Exception as e:
        print(f"ERROR /signup: {e}")
        flash("Something went wrong. Please try again.")
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
    u = get_user_record()
    if u and not u.session_token:
        u.session_token = uuid.uuid4().hex
        db.session.commit()
    session_token = u.session_token if u else None
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


            try:
                import threading as _threading

                # Pass current active_chat as history so the AI has memory
                current_chat = get_session_active_chat()

                # Run ask_ai in a thread with a 60s hard timeout
                _result = {"answer": None}
                def _run():
                    _result["answer"] = ask_ai(
                        question, subject, model,
                        chat_history=current_chat
                    )
                _t = _threading.Thread(target=_run, daemon=True)
                _t.start()
                _t.join(timeout=60)

                if _t.is_alive() or not _result["answer"]:
                    answer = (
                        "⚠️ The AI is temporarily unavailable or took too long to respond. "
                        "Please try again in a moment."
                    )
                else:
                    answer = _result["answer"]

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
                        is_active=True
                    )
                    db.session.add(msg)
                    db.session.commit()
                session.modified = True
                _persist_user()
                is_new_answer = True

            except Exception as _exc:
                print(f"ERROR dashboard ask_ai: {_exc}")
                import traceback
                traceback.print_exc()
                answer = (
                    "⚠️ An error occurred while getting an AI response. "
                    "Please try again."
                )
                error = None   # show the answer, not a form error
                is_new_answer = True

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
            if error:
                from flask import jsonify
                return jsonify({"error": error}), 400
            
            time_str = "Just now"
            if u and 'msg' in locals() and msg.created_at:
                time_str = msg.created_at.strftime("%b %d, %Y %I:%M %p")
                
            from flask import jsonify
            return jsonify({
                "question": question,
                "answer": answer,
                "model": model.capitalize() if model else "Unknown",
                "time": time_str
            })

    return render_template(
        "dashboard.html",
        user=user, name=name, subjects=SUBJECTS,
        answer=answer, question=question, subject=subject,
        model=model, error=error,
        default_subject=settings.get("default_subject", "Math"),
        groq_enabled=bool(os.getenv("GROQ_API_KEY", "").strip()),
        gemini_enabled=bool(os.getenv("GEMINI_API_KEY", "").strip()),
        chat_history=get_session_active_chat(),
        is_new_answer=is_new_answer,
        session_token=session_token,
    )


# ── History ───────────────────────────────────────────────────────────────────

@app.route("/history")
@login_required
def history():
    try:
        try:
            history_data = get_session_history()
        except Exception as db_err:
            print(f"ERROR /history DB: {db_err}")
            history_data = []
        return render_template(
            "history.html",
            user=get_current_user(),
            name=session.get("display_name", ""),
            history=history_data,
        )
    except Exception as e:
        print(f"ERROR /history: {e}")
        return render_template(
            "history.html",
            user=get_current_user(),
            name=session.get("display_name", ""),
            history=[],
        )


# ── Profile ───────────────────────────────────────────────────────────────────

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    try:
        user = get_current_user()
        if request.method == "POST":
            full_name = request.form.get("first_name", "").strip()
            if full_name:
                session["display_name"] = full_name
                session.modified = True
                try:
                    _persist_user()
                except Exception as db_err:
                    print(f"ERROR /profile DB save: {db_err}")
                flash("Name updated successfully! 🎉")
                return redirect(url_for("profile"))
        try:
            history_data = get_session_history()
        except Exception as db_err:
            print(f"ERROR /profile DB history: {db_err}")
            history_data = []
        return render_template(
            "profile.html",
            user=user,
            name=session.get("display_name", user["name"]),
            question_count=len(history_data),
            history=history_data,
            session=session,
        )
    except Exception as e:
        print(f"ERROR /profile: {e}")
        flash("Something went wrong loading your profile.")
        return redirect(url_for("dashboard"))


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
    )


# ── About ─────────────────────────────────────────────────────────────────────

@app.route("/about")
def about():
    try:
        return render_template("about.html", user=get_current_user())
    except Exception as e:
        print(f"ERROR /about: {e}")
        return render_template("about.html", user=None)


# ── Logout ────────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    try:
        _persist_user()
    except Exception as e:
        print(f"ERROR /logout persist: {e}")
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


# ─── Global Error Handlers ────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
       "application/json" in request.headers.get("Accept", ""):
        return jsonify({"error": "Page not found."}), 404
    # For browser requests, redirect to landing
    flash("That page was not found.")
    return redirect(url_for("landing")), 404


@app.errorhandler(500)
def server_error(e):
    print(f"GLOBAL 500 ERROR: {e}")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
       "application/json" in request.headers.get("Accept", ""):
        return jsonify({"error": "Something went wrong. Please try again."}), 500
    flash("Something went wrong on our end. Please try again.")
    try:
        return redirect(url_for("landing"))
    except Exception:
        return "Something went wrong. Please refresh the page.", 500


@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    print(f"UNHANDLED EXCEPTION: {e}")
    traceback.print_exc()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
       "application/json" in request.headers.get("Accept", ""):
        return jsonify({"error": "Something went wrong. Please try again."}), 500
    flash("Something went wrong. Please try again.")
    try:
        return redirect(url_for("landing"))
    except Exception:
        return "Something went wrong. Please refresh the page.", 500


# ─── Run ──────────────────────────────────────────────────────────────────────

from flutter_api import flutter_bp
app.register_blueprint(flutter_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
