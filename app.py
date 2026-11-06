import os
import re
import uuid
import requests as req
from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify, g
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash


# ─── Load .env ────────────────────────────────────────────────────────────────
# Load all the hidden secret keys from the .env file so we can use them securely
load_dotenv()

# ─── App setup ────────────────────────────────────────────────────────────────
# Create the main Flask web server application. "__name__" tells Flask where to look for templates and static files.
app = Flask(__name__)
# This fixes a bug when deploying to cloud servers (like Render) so the app knows it's using secure HTTPS.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
# Set a secure, random key used to encrypt the user's session cookie so hackers can't forge logins.
app.secret_key = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY") or "dev-secret-change-me"
# Allow Google OAuth to run without HTTPS locally during testing (never in production / Render)
if os.getenv("FLASK_ENV") != "production" and not os.getenv("RENDER"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

# Grab the database connection URL from the hidden .env file
db_url = os.getenv("DATABASE_URL")
# SQLAlchemy requires the URL to start with "postgresql://" not "postgres://", so we fix it if needed.
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Tell our Flask app exactly where the PostgreSQL database lives.
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
# Turn off a feature that tracks every single database change to save memory and make the app run faster.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Database engine options to prevent connections from timing out when deployed
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 280,
    "pool_pre_ping": True,
}
# Connect our Flask app to the SQLAlchemy database manager
db = SQLAlchemy(app)


class User(db.Model):
    """
    This is the User table in our database.
    It stores all the account details and preferences for people who sign up.
    """
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
    """
    This is the Message table in our database.
    It saves the chat history (the question the student asked, and the answer the AI gave).
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.String(36), nullable=True)
    subject = db.Column(db.String(100))
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# This block runs when the app starts. It ensures the database tables are created.
with app.app_context():
    try:
        db.create_all()
    except Exception as _db_init_err:
        print(f"WARN db.create_all(): {_db_init_err}")


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
    """
    Looks up the currently logged-in user in the database.
    Returns the User object if found, or None if they are not logged in.
    """
    if "user" not in session: 
        return None
    email = session["user"].get("email")
    if not email: return None
    u = User.query.filter_by(email=email).first()
    return u

def _format_model_name(raw_model: str) -> str:
    """Formats stored model_used strings cleanly without lowercasing custom model labels."""
    if not raw_model:
        return "Groq Llama 3"
    low = raw_model.strip().lower()
    if low == "groq":
        return "Groq Llama 3"
    if low == "gemini":
        return "Gemini"
    return raw_model.strip()


def _time_ago(dt):
    """Turns a UTC database timestamp into accurate relative or local-timezone text."""
    if not dt:
        return "Just now"
    secs = max(0, int((datetime.utcnow() - dt).total_seconds()))
    if secs < 60:
        return "Just now"
    mins = secs // 60
    if mins < 60:
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    hrs = mins // 60
    if hrs < 24:
        return f"{hrs} hour{'s' if hrs != 1 else ''} ago"
    days = hrs // 24
    if days < 7:
        return f"{days} day{'s' if days != 1 else ''} ago"
    try:
        from datetime import timezone as _tz
        local_dt = dt.replace(tzinfo=_tz.utc).astimezone()
        return local_dt.strftime("%b %d, %I:%M %p")
    except Exception:
        return dt.strftime("%b %d")


def get_session_history():
    """
    Gets a list of past chats for the logged-in user to display on the History page.
    It groups them by chat_id so we only show the first message of each conversation.
    """
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
            "model": _format_model_name(m.model_used),
            "time": _time_ago(m.created_at)
        })
        
        if len(chats) >= 100:
            break
            
    return chats

def get_session_active_chat():
    """
    Gets all the messages for the current conversation the user is looking at.
    This lets them read their previous back-and-forth messages on the Dashboard.
    """
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
        "model": _format_model_name(m.model_used),
        "time": _time_ago(m.created_at)
    } for m in msgs]

# ─── Auth helpers ─────────────────────────────────────────────────────────────

def get_current_user():
    """
    Quickly checks if a user is currently logged in via their session cookie.
    """
    return session.get("user")

def login_required(f):
    """
    This is a special wrapper (decorator) for our private routes (like Dashboard).
    If a user is not logged in, it instantly kicks them back to the landing page.
    """
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


# ─── Sidebar helpers (UI only) ────────────────────────────────────────────────

@app.context_processor
def inject_sidebar_helpers():
    """
    Gives the new sidebar layout (app_base.html) a read-only list of recent chats.
    It's a function so the database is only queried by pages that actually call it.
    """
    def sidebar_recents(limit=8):
        try:
            u = get_user_record()
            if not u:
                return []
            rows = (
                db.session.query(Message.chat_id, Message.question, Message.subject, Message.created_at)
                .filter(Message.user_id == u.id, Message.chat_id.isnot(None))
                .order_by(Message.created_at.desc())
                .limit(300)
                .all()
            )
        except Exception as exc:
            db.session.rollback()
            print(f"ERROR sidebar_recents: {exc}")
            return []

        # Newest activity first. Walking newest -> oldest, the title ends up as the
        # first question the student asked in that chat.
        chats = {}
        for chat_id, question, subject, created_at in rows:
            if chat_id not in chats:
                chats[chat_id] = {
                    "chat_id": chat_id,
                    "subject": subject or "",
                    "time": _time_ago(created_at),
                }
            chats[chat_id]["title"] = " ".join((question or "").split())[:90] or "Untitled chat"
        return list(chats.values())[:limit]

    return {
        "sidebar_recents": sidebar_recents,
        "active_chat_id": session.get("active_chat_id"),
    }


# ─── AI helper & Custom API Provider Catalog ──────────────────────────────────

CUSTOM_PROVIDER_CATALOG = {
    "groq": {
        "label": "Groq",
        "placeholder": "gsk_...",
        "models": [
            {"id": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B Versatile"},
            {"id": "llama-3.1-8b-instant", "label": "Llama 3.1 8B Instant"},
            {"id": "gemma2-9b-it", "label": "Gemma 2 9B"},
        ],
    },
    "gemini": {
        "label": "Google Gemini",
        "placeholder": "AIzaSy...",
        "models": [
            {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
            {"id": "gemini-2.5-pro", "label": "Gemini 2.5 Pro"},
            {"id": "gemini-2.0-flash", "label": "Gemini 2.0 Flash"},
            {"id": "gemini-2.0-flash-lite", "label": "Gemini 2.0 Flash Lite"},
        ],
    },
    "claude": {
        "label": "Anthropic Claude",
        "placeholder": "sk-ant-api03-...",
        "models": [
            {"id": "claude-sonnet-4-20250514", "label": "Claude Sonnet 4"},
            {"id": "claude-3-7-sonnet-latest", "label": "Claude 3.7 Sonnet"},
            {"id": "claude-3-5-haiku-latest", "label": "Claude 3.5 Haiku"},
        ],
    },
    "openai": {
        "label": "OpenAI",
        "placeholder": "sk-proj-...",
        "models": [
            {"id": "gpt-4.1", "label": "GPT-4.1"},
            {"id": "gpt-4.1-mini", "label": "GPT-4.1 mini"},
            {"id": "gpt-4o", "label": "GPT-4o"},
            {"id": "gpt-4o-mini", "label": "GPT-4o mini"},
            {"id": "o3-mini", "label": "o3-mini"},
        ],
    },
}


import base64
import hashlib
import hmac
import secrets


def _get_encryption_secret(user_email: str = "") -> bytes:
    """
    Derives a 32-byte server secret bound to the specific logged-in user's email
    so one user's encrypted API key can never be decrypted by any other user.
    """
    raw = (app.secret_key or os.getenv("FLASK_SECRET_KEY", "fallback-secret-key")).encode("utf-8")
    email_salt = (user_email or "").strip().lower().encode("utf-8")
    return hashlib.sha256(raw + b"::ash-api-key-vault-v2::" + email_salt).digest()


def _current_user_email() -> str:
    try:
        u = session.get("user") or {}
        return (u.get("email") or "").strip().lower()
    except Exception:
        return ""


def encrypt_api_key(plaintext: str, user_email: str = "") -> str:
    """Encrypts a user API key using PBKDF2-SHA256 stream cipher + HMAC-SHA256 authentication bound to the user."""
    pt = (plaintext or "").strip().encode("utf-8")
    if not pt:
        return ""
    email = user_email or _current_user_email()
    secret = _get_encryption_secret(email)
    nonce = secrets.token_bytes(16)
    keystream = hashlib.pbkdf2_hmac("sha256", secret, nonce + b"enc", 10000, dklen=len(pt))
    ct = bytes(a ^ b for a, b in zip(pt, keystream))
    tag = hmac.new(secret, nonce + ct, hashlib.sha256).digest()
    return "enc2:" + base64.urlsafe_b64encode(nonce + tag + ct).decode("ascii")


def decrypt_api_key(token: str, user_email: str = "") -> str:
    """Decrypts and verifies an encrypted user API key token for the specific user."""
    if not token or not isinstance(token, str):
        return ""
    token = token.strip()
    email = user_email or _current_user_email()
    if token.startswith("enc2:"):
        try:
            raw = base64.urlsafe_b64decode(token[5:].encode("ascii"))
            if len(raw) <= 48:
                return ""
            nonce, tag, ct = raw[:16], raw[16:48], raw[48:]
            secret = _get_encryption_secret(email)
            expected_tag = hmac.new(secret, nonce + ct, hashlib.sha256).digest()
            if not hmac.compare_digest(expected_tag, tag):
                return ""
            keystream = hashlib.pbkdf2_hmac("sha256", secret, nonce + b"enc", 10000, dklen=len(ct))
            pt = bytes(a ^ b for a, b in zip(ct, keystream))
            return pt.decode("utf-8")
        except Exception:
            return ""
    elif token.startswith("enc1:"):
        try:
            raw = base64.urlsafe_b64decode(token[5:].encode("ascii"))
            if len(raw) <= 48:
                return ""
            nonce, tag, ct = raw[:16], raw[16:48], raw[48:]
            legacy_secret = hashlib.sha256(
                (app.secret_key or os.getenv("FLASK_SECRET_KEY", "fallback-secret-key")).encode("utf-8")
                + b"::ash-api-key-vault-v1"
            ).digest()
            expected_tag = hmac.new(legacy_secret, nonce + ct, hashlib.sha256).digest()
            if not hmac.compare_digest(expected_tag, tag):
                return ""
            keystream = hashlib.pbkdf2_hmac("sha256", legacy_secret, nonce + b"enc", 10000, dklen=len(ct))
            pt = bytes(a ^ b for a, b in zip(ct, keystream))
            return pt.decode("utf-8")
        except Exception:
            return ""
    return ""


def mask_api_key(plaintext: str) -> str:
    """Returns a safe masked preview (e.g. 'AIza••••••••••••7f9a') that never exposes the secret."""
    k = (plaintext or "").strip()
    if not k:
        return ""
    if len(k) <= 12:
        return k[:3] + "••••••••"
    prefix_len = 7 if k.startswith("sk-ant-") else 4
    return f"{k[:prefix_len]}••••••••••••{k[-4:]}"


def get_saved_custom_api_key(settings: dict = None) -> str:
    """
    Retrieves and decrypts the logged-in user's saved custom API key strictly from the
    server-side PostgreSQL User record so the encrypted key never sits in browser cookies.
    """
    try:
        u = get_user_record()
        if u and isinstance(u.settings, dict):
            enc = u.settings.get("custom_api_key_enc", "")
            if enc:
                decrypted = decrypt_api_key(enc, u.email)
                if decrypted:
                    return decrypted
    except Exception:
        pass
    if settings and isinstance(settings, dict):
        enc = settings.get("custom_api_key_enc", "")
        if enc:
            return decrypt_api_key(enc)
    return ""


def save_user_encrypted_api_key(plaintext_key: str, settings: dict) -> None:
    """
    Encrypts the user's API key bound to their account email, saves the ciphertext ONLY
    in the server-side PostgreSQL database (`User.settings`), and strips all key material
    from the client-side `session['settings']` cookie so it is never exposed in the browser.
    """
    raw = (plaintext_key or "").strip()
    email = _current_user_email()
    enc = encrypt_api_key(raw, email) if raw else ""
    masked = mask_api_key(raw) if raw else ""

    # Never keep raw or encrypted key inside browser session cookie
    settings.pop("custom_api_key", None)
    settings.pop("custom_api_key_enc", None)
    settings["custom_key_masked"] = masked
    settings["has_custom_api"] = bool(raw)

    u = get_user_record()
    if u:
        db_settings = dict(u.settings) if isinstance(u.settings, dict) else {}
        db_settings.update(settings)
        db_settings.pop("custom_api_key", None)
        if enc:
            db_settings["custom_api_key_enc"] = enc
        else:
            db_settings.pop("custom_api_key_enc", None)
        u.settings = db_settings
        db.session.commit()


def has_saved_custom_api_key(settings: dict = None) -> bool:
    """Returns True if the logged-in user has a valid encrypted custom API key stored."""
    return bool(get_saved_custom_api_key(settings))


def get_masked_custom_api_key(settings: dict = None) -> str:
    """Returns only the masked representation of the user's saved key for UI display."""
    raw = get_saved_custom_api_key(settings)
    if raw:
        return mask_api_key(raw)
    if settings and settings.get("custom_key_masked"):
        return settings["custom_key_masked"]
    return ""


def detect_provider_from_key(api_key: str, fallback_provider: str = "claude") -> str:
    """Auto-detects the AI provider from the key prefix if recognizable."""
    k = (api_key or "").strip()
    if k.startswith("AIza") or k.startswith("AQ."):
        return "gemini"
    if k.startswith("sk-ant-"):
        return "claude"
    if k.startswith("gsk_"):
        return "groq"
    if k.startswith("sk-"):
        return "openai"
    return (fallback_provider or "claude").strip().lower()


def validate_and_verify_api_key(provider: str, api_key: str, model_name: str = "") -> tuple:
    """
    Validates that an API key is genuinely formatted for the chosen provider AND verifies it
    against the live provider API so fake or inactive keys are rejected immediately.
    Returns (is_valid: bool, message: str, detected_provider: str).
    """
    key = (api_key or "").strip()
    prov = detect_provider_from_key(key, provider)
    prov_label = CUSTOM_PROVIDER_CATALOG.get(prov, {}).get("label", prov.capitalize())

    if not key:
        return False, "Please paste your API key first.", prov
    if any(ch.isspace() for ch in key):
        return False, "Invalid API key: keys cannot contain spaces or line breaks.", prov
    if len(key) < 24:
        return False, f"Invalid {prov_label} API key: key is too short to be a real API key.", prov

    # Reject obvious fake / placeholder strings
    lower_key = key.lower()
    for fake_word in ("fake", "testkey", "example", "your_key", "your-key", "12345678", "abcdef"):
        if fake_word in lower_key:
            return False, f"Invalid {prov_label} API key: placeholder or test strings are not allowed.", prov

    # Provider-specific prefix & structure checks
    if prov == "claude":
        if not key.startswith("sk-ant-"):
            return False, "Invalid Anthropic Claude API key: Claude keys must start with 'sk-ant-'.", prov
        if len(set(key[7:])) < 8:
            return False, "Invalid Anthropic Claude API key: key appears to be fake.", prov
    elif prov == "openai":
        if not key.startswith("sk-") or key.startswith("sk-ant-"):
            return False, "Invalid OpenAI API key: OpenAI keys must start with 'sk-' (and not 'sk-ant-').", prov
        if len(set(key[3:])) < 8:
            return False, "Invalid OpenAI API key: key appears to be fake.", prov
    elif prov == "gemini":
        if not (key.startswith("AIza") or key.startswith("AQ.")) or len(key) < 30:
            return False, "Invalid Google Gemini API key: Gemini keys must start with 'AIza' and be ~39 characters.", prov
        if len(set(key[4:])) < 8:
            return False, "Invalid Google Gemini API key: key appears to be fake.", prov
    elif prov == "groq":
        if not key.startswith("gsk_") or len(key) < 28:
            return False, "Invalid Groq API key: Groq keys must start with 'gsk_'.", prov
        if len(set(key[4:])) < 8:
            return False, "Invalid Groq API key: key appears to be fake.", prov
    else:
        return False, f"Unsupported AI provider '{prov}'.", prov

    # Live verification call against the provider's official models endpoint (never 404s on model IDs)
    try:
        if prov == "gemini":
            # Verify via GET /v1beta/models using header-only authentication so key never appears in URLs
            resp = req.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                headers={"x-goog-api-key": key},
                params={"pageSize": 5},
                timeout=12,
            )
            if resp.status_code in (400, 401, 403):
                err_detail = ""
                try:
                    err_detail = resp.json().get("error", {}).get("message", "")
                except Exception:
                    pass
                return False, f"Rejected by Google Gemini: {err_detail or 'this API key is invalid or unauthorized.'}", prov
            if not resp.ok:
                return False, f"Google Gemini verification failed (HTTP {resp.status_code}). Please check your key.", prov
            return True, f"Verified! Your Google Gemini key ({mask_api_key(key)}) is active and protected.", prov

        elif prov == "claude":
            resp = req.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                },
                timeout=12,
            )
            if resp.status_code in (401, 403):
                return False, "Rejected by Anthropic: this Claude API key is invalid or unauthorized.", prov
            if not resp.ok:
                err_msg = ""
                try:
                    err_msg = resp.json().get("error", {}).get("message", "")
                except Exception:
                    pass
                return False, f"Anthropic verification failed: {err_msg or f'HTTP {resp.status_code}'}", prov
            return True, f"Verified! Your Anthropic Claude key ({mask_api_key(key)}) is active and protected.", prov

        elif prov == "openai":
            resp = req.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=12,
            )
            if resp.status_code in (401, 403):
                return False, "Rejected by OpenAI: this API key is invalid or unauthorized.", prov
            if not resp.ok:
                return False, f"OpenAI verification failed (HTTP {resp.status_code}).", prov
            return True, f"Verified! Your OpenAI key ({mask_api_key(key)}) is active and protected.", prov

        elif prov == "groq":
            resp = req.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=12,
            )
            if resp.status_code in (401, 403):
                return False, "Rejected by Groq: this API key is invalid or unauthorized.", prov
            if not resp.ok:
                return False, f"Groq verification failed (HTTP {resp.status_code}).", prov
            return True, f"Verified! Your Groq key ({mask_api_key(key)}) is active and protected.", prov

    except Exception as e:
        print(f"API key verification network error ({prov}): {type(e).__name__}")
        return False, f"Could not reach {prov_label} to verify the key. Please check your internet connection.", prov

    return True, "API key verified.", prov


def get_model_display_label(model_key, settings=None):
    """Returns a friendly display name for the active AI model."""
    settings = settings or {}
    if model_key == "custom" or str(model_key).startswith("custom:"):
        prov = settings.get("custom_provider", "claude")
        prov_info = CUSTOM_PROVIDER_CATALOG.get(prov, {"label": prov.capitalize(), "models": []})
        mod_id = settings.get("custom_model", "")
        for m in prov_info.get("models", []):
            if m["id"] == mod_id:
                return f"{m['label']} (Your Key)"
        if mod_id:
            return f"{prov_info['label']} · {mod_id}"
        return f"{prov_info['label']} (Your Key)"
    if model_key == "gemini":
        return "Gemini"
    return "Groq Llama 3"


def _discover_gemini_models(key: str, prefer_pro: bool = False) -> list:
    """
    Queries GET /v1beta/models with the user's API key to discover the exact
    generateContent-capable Gemini models active on their account right now.
    """
    try:
        resp = req.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            headers={"x-goog-api-key": key},
            params={"pageSize": 100},
            timeout=10,
        )
        if not resp.ok:
            return []
        models_data = resp.json().get("models", [])
        usable = []
        skip_tokens = ("embedding", "imagen", "veo", "aqa", "tts", "audio", "vision", "robotics", "computer-use", "learnlm")
        for m in models_data:
            methods = m.get("supportedGenerationMethods") or []
            if "generateContent" not in methods:
                continue
            name = (m.get("name") or "").replace("models/", "").strip()
            if not name.startswith("gemini"):
                continue
            if any(tok in name.lower() for tok in skip_tokens):
                continue
            usable.append(name)

        # Sort so newer versions and preferred tier (pro vs flash) come first
        def _score(mod_name: str):
            low = mod_name.lower()
            tier_match = 1 if (("pro" in low) == prefer_pro or ("flash" in low and not prefer_pro)) else 0
            not_exp = 0 if ("exp" in low or "preview" in low) else 1
            return (tier_match, not_exp, low)

        usable.sort(key=_score, reverse=True)
        return usable
    except Exception as e:
        print(f"Gemini model discovery error: {type(e).__name__}")
        return []


def ask_groq(messages, api_key=None, model_name="llama-3.3-70b-versatile"):
    """
    Sends the user's question to the Groq API (using the Llama 3 model).
    Automatically falls back across active Groq models or discovers live models via /v1/models.
    """
    key = (api_key or os.getenv("GROQ_API_KEY", "")).strip()
    if not key:
        return None
    primary = (model_name or "llama-3.3-70b-versatile").strip()
    candidates = [primary] + [
        m for m in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it")
        if m != primary
    ]
    tried = set()
    for candidate in candidates:
        tried.add(candidate)
        try:
            resp = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": candidate,
                    "messages": messages,
                    "max_tokens": 4000,
                },
                timeout=45,
            )
            if resp.ok:
                return resp.json()["choices"][0]["message"]["content"].strip()
            elif resp.status_code in (401, 403):
                print(f"Groq auth error {resp.status_code}")
                return None
            else:
                print(f"Groq API error {resp.status_code} ({candidate}): {resp.text[:160]}")
        except Exception as e:
            print(f"Groq error ({candidate}): {type(e).__name__}")

    # Dynamic fallback: discover active chat models from Groq /v1/models
    try:
        m_resp = req.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        if m_resp.ok:
            for item in m_resp.json().get("data", []):
                mid = (item.get("id") or "").strip()
                if not mid or mid in tried or any(x in mid.lower() for x in ("whisper", "tts", "guard", "embed", "vision")):
                    continue
                resp = req.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": mid, "messages": messages, "max_tokens": 4000},
                    timeout=45,
                )
                if resp.ok:
                    return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Groq dynamic fallback error: {type(e).__name__}")
    return None


_WORKING_GEMINI_MODEL_CACHE = {}


def ask_gemini(messages, api_key=None, model_name="gemini-2.5-flash"):
    """
    Sends the user's question to the Google Gemini API.
    Dynamically discovers live generateContent models for the key if a model ID is retired or 404s,
    and caches the working model per key so subsequent messages succeed on the first call.
    """
    import re as _re
    key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    if not key:
        return None
    primary = (model_name or "gemini-2.5-flash").strip().replace("models/", "")
    prefer_pro = "pro" in primary.lower()
    cache_key = (key[:16], prefer_pro)
    cached_working = _WORKING_GEMINI_MODEL_CACHE.get(cache_key)

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

    # Discover live models directly supported by this key on Google's API
    discovered = _discover_gemini_models(key, prefer_pro=prefer_pro)
    seed_list = (
        ([cached_working] if cached_working else [])
        + [primary]
        + (["gemini-pro-latest", "gemini-flash-latest"] if prefer_pro else ["gemini-flash-latest", "gemini-pro-latest"])
        + ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.0-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
        + discovered
    )
    candidates = []
    for m in seed_list:
        if m and m not in candidates:
            candidates.append(m)

    tried = set()
    idx = 0
    while idx < len(candidates):
        candidate = candidates[idx]
        idx += 1
        if candidate in tried:
            continue
        tried.add(candidate)
        try:
            resp = req.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{candidate}:generateContent",
                headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                json={"contents": contents},
                timeout=45,
            )
            if resp.ok:
                data = resp.json()
                cands = data.get("candidates") or []
                if cands and cands[0].get("content", {}).get("parts"):
                    _WORKING_GEMINI_MODEL_CACHE[cache_key] = candidate
                    return cands[0]["content"]["parts"][0].get("text", "").strip()
            elif resp.status_code in (401, 403):
                print(f"Gemini auth error {resp.status_code}: {resp.text[:200]}")
                break
            else:
                full_err = resp.text or ""
                print(f"Gemini API error {resp.status_code} ({candidate}): {full_err[:350]}")
                # If Google's error message tells us the exact replacement model (e.g. 'use models/gemini-...'), try it immediately next!
                for suggested in _re.findall(r"models/([a-zA-Z0-9._-]+)", full_err):
                    clean_sug = suggested.strip().rstrip(".,;\"'")
                    if clean_sug and clean_sug != candidate and clean_sug not in tried:
                        if clean_sug in candidates:
                            candidates.remove(clean_sug)
                        candidates.insert(idx, clean_sug)
        except Exception as e:
            print(f"Gemini error ({candidate}): {type(e).__name__}")
    return None


def ask_claude(messages, api_key, model_name="claude-sonnet-4-20250514"):
    """Sends the user's question to Anthropic Claude using the student's own API key, with live model discovery fallback."""
    key = (api_key or "").strip()
    if not key:
        return None
    target_model = (model_name or "claude-sonnet-4-20250514").strip()
    system_text = ""
    chat_msgs = []
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        elif msg["role"] in ("user", "assistant"):
            chat_msgs.append({"role": msg["role"], "content": msg["content"]})

    candidates = [target_model]
    try:
        m_resp = req.get(
            "https://api.anthropic.com/v1/models",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
            timeout=10,
        )
        if m_resp.ok:
            for item in m_resp.json().get("data", []):
                mid = (item.get("id") or "").strip()
                if mid and mid not in candidates:
                    candidates.append(mid)
    except Exception:
        pass

    for candidate in candidates[:5]:
        try:
            payload = {
                "model": candidate,
                "max_tokens": 4000,
                "messages": chat_msgs,
            }
            if system_text:
                payload["system"] = system_text
            resp = req.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=45,
            )
            if resp.ok:
                data = resp.json()
                blocks = data.get("content", [])
                if blocks and isinstance(blocks, list):
                    return blocks[0].get("text", "").strip()
            elif resp.status_code in (401, 403):
                break
            else:
                print(f"Claude API error {resp.status_code} ({candidate}): {resp.text[:200]}")
        except Exception as e:
            print(f"Claude error ({candidate}): {type(e).__name__}")
    return None


def ask_openai(messages, api_key, model_name="gpt-4.1-mini"):
    """Sends the user's question to OpenAI using the student's own API key, with automatic fallback."""
    key = (api_key or "").strip()
    if not key:
        return None
    target_model = (model_name or "gpt-4.1-mini").strip()
    candidates = [target_model] + [m for m in ("gpt-4.1-mini", "gpt-4.1", "gpt-4o", "gpt-4o-mini") if m != target_model]
    for candidate in candidates:
        try:
            resp = req.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": candidate,
                    "messages": messages,
                    "max_tokens": 4000,
                },
                timeout=45,
            )
            if resp.ok:
                return resp.json()["choices"][0]["message"]["content"].strip()
            elif resp.status_code in (401, 403):
                break
            else:
                print(f"OpenAI API error {resp.status_code} ({candidate}): {resp.text[:200]}")
        except Exception as e:
            print(f"OpenAI error ({candidate}): {type(e).__name__}")
    return None


def ask_ai(question, subject, model="groq", chat_history=None, custom_config=None, user_settings=None):
    """
    This is our main AI function. It takes the student's question and past chat history,
    builds a prompt tailored to the student's Settings preferences, and asks either the
    user's custom API key or our built-in Groq/Gemini.
    """
    prefs = user_settings or {}
    grade_map = {
        "middle_school": "a Middle School student (Grades 6–8, simple analogies and clear foundational vocabulary)",
        "high_school": "a High School / AP student (Grades 9–12, clear concepts with structured rigor)",
        "college": "a College / University student (undergraduate academic depth and formal terminology)",
        "graduate": "a Graduate / Advanced researcher (rigorous, in-depth technical explanations)",
    }
    tone_map = {
        "step_by_step": "Break down explanations step-by-step with numbered stages.",
        "socratic": "Use a friendly Socratic coaching style that guides the student's reasoning while answering.",
        "direct": "Provide direct, to-the-point explanations without unnecessary filler.",
        "eli5": "Explain concepts as simply as possible using everyday real-world examples.",
    }
    length_map = {
        "concise": "Keep the response concise and brief (1–2 short paragraphs or bullet points).",
        "balanced": "Keep the response balanced in length—thorough enough to understand clearly without being overly long.",
        "detailed": "Provide a comprehensive, detailed breakdown with worked examples and deeper context.",
    }
    grade_desc = grade_map.get(prefs.get("grade_level", "high_school"), grade_map["high_school"])
    tone_desc = tone_map.get(prefs.get("ai_tone", "step_by_step"), tone_map["step_by_step"])
    length_desc = length_map.get(prefs.get("response_length", "balanced"), length_map["balanced"])
    practice_desc = (
        "\n- At the end of your explanation, include 1 short practice problem (with a hidden/brief hint) so the student can test their understanding."
        if prefs.get("include_practice", False)
        else ""
    )

    system_content = (
        "You are 'AI Student Helper' (also known as 'I Student Helper'), a premium AI-powered homework helper "
        "and study companion web application. Explain things simply, concisely, and clearly to the student. "
        "When answering math questions, use proper mathematical notation. For inline math use \\( ... \\) "
        "and for block/display equations use \\[ ... \\] so they render beautifully.\n"
        f"Student Learning Preferences:\n"
        f"- Target Academic Level: Tailor your explanation for {grade_desc}.\n"
        f"- Teaching Style: {tone_desc}\n"
        f"- Response Length: {length_desc}{practice_desc}\n"
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

    answer = None

    # ── 1. Check if the user selected their own Custom API Key ────────────────────
    if custom_config and custom_config.get("api_key") and (
        model == "custom" or custom_config.get("use_custom_api")
    ):
        c_prov = custom_config.get("provider", "claude")
        c_model = custom_config.get("model", "")
        c_key = custom_config.get("api_key", "")
        if c_prov == "claude":
            answer = ask_claude(messages, c_key, c_model or "claude-sonnet-4-20250514")
        elif c_prov == "gemini":
            answer = ask_gemini(messages, api_key=c_key, model_name=c_model or "gemini-2.5-flash")
        elif c_prov == "groq":
            answer = ask_groq(messages, api_key=c_key, model_name=c_model or "llama-3.3-70b-versatile")
        elif c_prov == "openai":
            answer = ask_openai(messages, c_key, c_model or "gpt-4.1-mini")

        if not answer and model == "custom":
            return (
                f"Your custom {CUSTOM_PROVIDER_CATALOG.get(c_prov, {}).get('label', c_prov)} API key "
                f"could not complete the request. Please verify your API key and model in Settings -> API Keys."
            )

    # ── 2. Route to built-in models: Groq = primary, Gemini = silent fallback ─────
    if not answer:
        if model == "gemini":
            answer = ask_gemini(messages) or ask_groq(messages)
        else:  # groq (default)
            answer = ask_groq(messages) or ask_gemini(messages)

    if not answer:
        answer = (
            "AI is temporarily unavailable. Please try again in a moment."
        )
    return answer



# ─── Routes ────────────────────────────────────────────────────────────────────────

# ── Keep-alive ping (prevents Render free tier from sleeping) ───────────────

@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "AI Student Helper is alive"}), 200


def _sanitize_session_settings(raw_settings, default_subject="Math"):
    """Returns a clean copy of settings for the browser cookie with no secret material."""
    clean = dict(raw_settings) if isinstance(raw_settings, dict) else {"default_subject": default_subject or "Math"}
    clean.setdefault("default_subject", default_subject or "Math")
    clean.pop("custom_api_key", None)
    clean.pop("custom_api_key_enc", None)
    has_key = has_saved_custom_api_key(clean)
    clean["has_custom_api"] = has_key
    clean["custom_key_masked"] = get_masked_custom_api_key(clean) if has_key else ""
    return clean


@app.route("/")
def landing():
    """
    This is the very first page people see.
    If they are already logged in and onboarded, we send them straight to the Dashboard.
    If not, we show them the Welcome page.
    """
    try:
        # Step 1: Check if the user is already logged in and completed onboarding
        if get_current_user() and get_user_record() and not session.get("needs_setup"):
            return redirect(url_for("dashboard"))
            
        # Step 2: Show the landing page
        return render_template("landing.html")
    except Exception as e:
        print(f"ERROR /landing: {e}")
        return render_template("landing.html")


@app.route("/after-login")
def after_login():
    """
    Google sends the user here after they click 'Sign in with Google'.
    We verify their Google info and log them in or create an account for them.
    """
    try:
        # Step 1: Make sure Google actually authorized them
        if not google.authorized:
            return redirect(url_for("google.login"))

        # Step 2: Get their email and name from Google
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            flash("Could not fetch your Google account info. Please try again.")
            return redirect(url_for("landing"))

        info = resp.json()
        google_id = str(info.get("id"))
        email_clean = (info.get("email") or "").lower().strip()

        is_valid_email, email_err, email_clean = validate_signup_email(email_clean)
        if not is_valid_email:
            session.clear()
            flash(email_err)
            return redirect(url_for("signup"))

        # Step 3: Save their basic Google info into their session (browser cookie)
        session["user"] = {
            "email":   email_clean,
            "name":    info.get("name"),
            "picture": info.get("picture"),
            "id":      google_id,
        }

        # Step 4: Check if they already have an account in our database
        try:
            saved = User.query.filter_by(google_id=google_id).first()
            if not saved and email_clean:
                saved = find_user_by_email(email_clean)
                if saved:
                    saved.google_id = google_id
                    db.session.commit()
        except Exception as db_err:
            print(f"ERROR after_login DB lookup: {db_err}")
            saved = None

        # Step 5: Send them to Dashboard if they exist, otherwise to Setup screen
        if saved:
            session.pop("needs_setup", None)
            session["user"]["email"] = saved.email
            session["display_name"] = f"{saved.first_name or ''} {saved.last_name or ''}".strip() or info.get("name") or "Student"
            clean_settings = _sanitize_session_settings(saved.settings, saved.default_subject or "Math")
            session["settings"] = clean_settings
            session["active_subject"] = clean_settings.get("default_subject", "Math")
            session["active_model"] = clean_settings.get("preferred_model", "groq")
            return redirect(url_for("dashboard"))
        else:
            session["needs_setup"] = True
            return redirect(url_for("setup"))
    except Exception as e:
        print(f"ERROR /after-login: {e}")
        flash("Something went wrong during sign-in. Please try again.")
        return redirect(url_for("landing"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    """
    This is the final step of creating an account.
    We ask them for their name and favorite subject before going to the dashboard.
    """
    try:
        # Step 1: Make sure they are partially logged in from Google or Sign Up
        if "user" not in session:
            return redirect(url_for("landing"))
            
        if request.method == "POST":
            # Step 2: Get the info they typed in the form
            first   = request.form.get("first_name", "").strip()
            last    = request.form.get("last_name", "").strip()
            subject = request.form.get("default_subject", "Math")
            if subject not in SUBJECTS:
                subject = "Math"
            
            if first:
                display_name = f"{first} {last}".strip()
                session["display_name"] = display_name
                session["settings"] = {"default_subject": subject}
                session["active_subject"] = subject
                session["active_model"] = "groq"
                
                # Step 3: Save their new account in the database
                try:
                    email_clean = session["user"]["email"].lower().strip()
                    existing_user = User.query.filter_by(email=email_clean).first()
                    
                    if existing_user:
                        if not existing_user.google_id and session["user"].get("id"):
                            existing_user.google_id = session["user"]["id"]
                        existing_user.first_name = first
                        existing_user.last_name = last
                        existing_user.default_subject = subject
                        merged_settings = dict(existing_user.settings) if isinstance(existing_user.settings, dict) else {}
                        merged_settings["default_subject"] = subject
                        existing_user.settings = merged_settings
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
                    
                # Step 4: Successfully saved! Go to the Dashboard
                session.pop("needs_setup", None)
                return redirect(url_for("dashboard"))
                
        # If it's a GET request, just show the setup form
        return render_template("setup.html")
    except Exception as e:
        print(f"ERROR /setup: {e}")
        return render_template("setup.html")


# ── Email Validation & Anti-Temp-Mail Protection ──────────────────────────────

ALLOWED_EMAIL_DOMAINS = {
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "yahoo.com",
    "proton.me",
    "protonmail.com",
    "aol.com",
    "zoho.com",
}

BLOCKED_TEMP_EMAIL_DOMAINS = {
    "googlemail.com",
    "gmailnator.com",
    "smailpro.com",
    "tempmail.com",
    "temp-mail.org",
    "temp-mail.io",
    "10minutemail.com",
    "guerrillamail.com",
    "sharklasers.com",
    "mailinator.com",
    "yopmail.com",
    "trashmail.com",
    "getnada.com",
    "maildrop.cc",
    "dispostable.com",
    "mohmal.com",
    "fakeinbox.com",
    "throwawaymail.com",
    "emailondeck.com",
    "burnermail.io",
    "tempmailo.com",
    "internxt.com",
    "duck.com",
    "mozmail.com",
    " SimpleLogin.co".strip().lower(),
    "anonaddy.me",
}

BLOCKED_LOCAL_KEYWORDS = (
    "tempmail",
    "temp-mail",
    "gmailnator",
    "smailpro",
    "throwaway",
    "disposable",
    "burnermail",
    "trashmail",
    "10minutemail",
    "guerrillamail",
    "mailinator",
    "yopmail",
    "fakeemail",
)


def canonicalize_email(raw_email: str) -> str:
    """
    Return a canonical lowercase email for duplicate-account detection.
    For @gmail.com, dots in the local part are ignored by Google, so stripping
    dots ensures john.doe@gmail.com and johndoe@gmail.com map to the same user.
    """
    cleaned = (raw_email or "").strip().lower()
    if "@" not in cleaned:
        return cleaned
    local, domain = cleaned.rsplit("@", 1)
    local = local.split("+", 1)[0]
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def validate_signup_email(raw_email: str) -> tuple[bool, str, str]:
    """
    Validate that the email is a real, permanent email address (e.g. gmail.com,
    outlook.com) and block temporary/disposable emails including temporary
    Google/Gmail generator addresses (dot-trick permutations, + aliases,
    googlemail.com, and known burner patterns).
    Returns (is_valid, error_message, cleaned_email).
    """
    email = (raw_email or "").strip().lower()
    if not email or "@" not in email:
        return False, "Please enter a valid email address.", email

    parts = email.split("@")
    if len(parts) != 2:
        return False, "Please enter a valid email address.", email

    local, domain = parts[0].strip(), parts[1].strip()
    if not local or not domain or "." not in domain:
        return False, "Please enter a valid email address.", email

    # 1. Block '+' subaddressing used for temporary/disposable aliases
    if "+" in local:
        return (
            False,
            "Temporary or alias email addresses (containing '+') are not allowed. Please use your main email address.",
            email,
        )

    # 2. Block googlemail.com and known temporary email domains explicitly
    if domain == "googlemail.com":
        return (
            False,
            "Temporary Google mail aliases (@googlemail.com) are not allowed. Please use a standard @gmail.com or @outlook.com address.",
            email,
        )

    if domain in BLOCKED_TEMP_EMAIL_DOMAINS or any(
        k in domain for k in ("tempmail", "temp-mail", "gmailnator", "smailpro", "mailinator", "yopmail", "guerrilla", "10minute", "trashmail", "throwaway", "disposable")
    ):
        return (
            False,
            "Temporary or disposable email addresses are not allowed. Please use a permanent email such as Gmail or Outlook.",
            email,
        )

    # 3. Require an approved provider domain (gmail.com, outlook.com, etc. or .edu/.ac academic domain)
    is_academic = domain.endswith(".edu") or ".ac." in domain or domain.endswith(".edu.sa") or domain.endswith(".edu.uk")
    if domain not in ALLOWED_EMAIL_DOMAINS and not is_academic:
        return (
            False,
            "Please sign up with a permanent email provider such as Gmail (@gmail.com), Outlook (@outlook.com / @hotmail.com), iCloud, Yahoo, or a school (.edu) email.",
            email,
        )

    # 4. Block temporary Google/Gmail generator tricks (Gmailnator / Smailpro dot-matrix & burner patterns)
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False, "Please enter a valid email address.", email

    local_no_dots = local.replace(".", "")
    if len(local_no_dots) < 3 or not re.match(r"^[a-z0-9._-]+$", local):
        return False, "Please enter a valid email address.", email

    if any(kw in local_no_dots for kw in BLOCKED_LOCAL_KEYWORDS):
        return (
            False,
            "Temporary or disposable email addresses are not allowed. Please use your personal Gmail or Outlook account.",
            email,
        )

    if domain == "gmail.com":
        # Temp-Gmail generators (like Gmailnator/Smailpro) inject 3+ dots across the username
        # to create thousands of disposable addresses from one burner Gmail account.
        if local.count(".") > 2:
            return (
                False,
                "Temporary Google email addresses (excessive dot variations) are not allowed. Please use a standard @gmail.com or @outlook.com address.",
                email,
            )
        # Also block alternating single-character dot patterns like a.b.c@gmail.com
        segments = local.split(".")
        if len(segments) >= 3 and sum(1 for s in segments if len(s) == 1) >= 2:
            return (
                False,
                "Temporary Google email addresses are not allowed. Please use your real @gmail.com or @outlook.com address.",
                email,
            )

    return True, "", email


def find_user_by_email(raw_email: str):
    """
    Look up an existing User by exact email match OR canonical Gmail address
    so a user cannot register the same Gmail account multiple times using dots.
    """
    email = (raw_email or "").strip().lower()
    if not email:
        return None
    user_record = User.query.filter_by(email=email).first()
    if user_record:
        return user_record

    target_canonical = canonicalize_email(email)
    if target_canonical.endswith("@gmail.com"):
        gmail_users = User.query.filter(User.email.ilike("%@gmail.com")).all()
        for existing in gmail_users:
            if canonicalize_email(existing.email) == target_canonical:
                return existing
    return None


@app.route("/signin", methods=["GET", "POST"])
def signin():
    """
    This page lets users log in with their email and password.
    """
    try:
        # Step 1: If they are already logged in, send them to Dashboard
        u_sess = get_current_user()
        if u_sess and not session.get("needs_setup"):
            try:
                if find_user_by_email(u_sess.get("email")):
                    return redirect(url_for("dashboard"))
                else:
                    session.clear()
            except Exception:
                session.clear()
            
        if request.method == "POST":
            # Step 2: Get the email and password they typed
            email    = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            
            if not email or not password:
                flash("Please enter both email and password.")
                return render_template("signin.html", prefill_email=email)

            # Step 3: Look them up in the database (supports canonical Gmail lookup)
            try:
                user_record = find_user_by_email(email)
            except Exception as db_err:
                print(f"ERROR /signin DB: {db_err}")
                flash("Database temporarily unavailable. Please try again.")
                return render_template("signin.html", prefill_email=email)
                
            if not user_record:
                flash("No account found with this email. Please create an account first.")
                return render_template("signin.html", prefill_email=email)
                
            if not user_record.password:
                flash("This email is linked to Google Sign-In. Please click 'Continue with Google' above.")
                return render_template("signin.html", prefill_email=email)

            # Step 4: Check if the password matches (using secure hash comparison)
            if not check_password_hash(user_record.password, password):
                flash("Incorrect password. Please try again.")
                return render_template("signin.html", prefill_email=email)
                
            # Step 5: Success! Save their info in the session cookie and send straight to Dashboard
            session.pop("needs_setup", None)
            session["user"] = {
                "email": user_record.email,
                "name": f"{user_record.first_name or ''} {user_record.last_name or ''}".strip() or "Student",
                "picture": None,
                "id": user_record.google_id or str(uuid.uuid4())
            }
            session["display_name"] = session["user"]["name"]
            clean_settings = _sanitize_session_settings(user_record.settings, user_record.default_subject or "Math")
            session["settings"] = clean_settings
            session["active_subject"] = clean_settings.get("default_subject", "Math")
            session["active_model"] = clean_settings.get("preferred_model", "groq")
            
            return redirect(url_for("dashboard"))
            
        # If it's a GET request, just show the Sign In page (pre-filling email if redirected from signup)
        prefill_email = request.args.get("email", "").strip()
        return render_template("signin.html", prefill_email=prefill_email)
    except Exception as e:
        print(f"ERROR /signin: {e}")
        flash("Something went wrong. Please try again.")
        return render_template("signin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    This page lets new users create an account with an email and password.
    """
    try:
        # Step 1: If they are already logged in, send them to Dashboard
        u_sess = get_current_user()
        if u_sess and not session.get("needs_setup"):
            try:
                if find_user_by_email(u_sess.get("email")):
                    return redirect(url_for("dashboard"))
                else:
                    session.clear()
            except Exception:
                session.clear()
            
        if request.method == "POST":
            # Step 2: Read what they typed in the signup form
            first_name = request.form.get("first_name", "").strip()
            last_name  = request.form.get("last_name", "").strip()
            email      = request.form.get("email", "").strip().lower()
            password   = request.form.get("password", "")
            confirm    = request.form.get("confirm_password", "")
            
            if not first_name or not email or not password:
                flash("Please fill in all required fields.")
                return render_template("signup.html")
                
            # Step 2b: Validate email and block temporary / disposable Google or third-party emails
            is_valid_email, email_err, email = validate_signup_email(email)
            if not is_valid_email:
                flash(email_err)
                return render_template("signup.html")

            if len(password) < 6:
                flash("Password must be at least 6 characters long.")
                return render_template("signup.html")

            if password != confirm:
                flash("Passwords do not match. Please try again.")
                return render_template("signup.html")

            # Step 3: Check if this email is already registered (including Gmail dot variations)
            try:
                user_record = find_user_by_email(email)
                if user_record:
                    flash("An account with this email already exists. Please sign in to continue to your dashboard.")
                    return redirect(url_for("signin", email=user_record.email))
                    
                # Step 4: Create their new account in the database (password is hashed for security)
                new_user = User(
                    google_id=None,
                    email=email,
                    password=generate_password_hash(password, method="pbkdf2:sha256"),
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
            
            # Step 5: Redirect to Sign In with their email pre-filled so they log in and go straight to Dashboard
            flash("Account created successfully! Please sign in to continue to your dashboard.")
            return redirect(url_for("signin", email=email))
            
        # If GET request, show the empty signup form
        return render_template("signup.html")
    except Exception as e:
        print(f"ERROR /signup: {e}")
        flash("Something went wrong. Please try again.")
        return render_template("signup.html")


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    """
    This is the main screen where the student asks questions and chats with the AI.
    It handles getting the answer, saving history, and starting new chats.
    """
    
    # Step 1: If the user clicked "Clear History"
    if request.args.get("clear"):
        u = get_user_record()
        if u:
            Message.query.filter_by(user_id=u.id).delete()
            db.session.commit()
        session.pop("active_chat_id", None)
        session.modified = True
        _persist_user()
        flash("All chat history cleared permanently.")
        return redirect(url_for("dashboard"))

    # Step 2: If the user clicked "New Chat"
    if request.args.get("new_chat"):
        session.pop("active_chat_id", None)
        u = get_user_record()
        if u:
            Message.query.filter_by(user_id=u.id, is_active=True).update({"is_active": False})
            db.session.commit()
        session.modified = True
        _persist_user()
        return redirect(url_for("dashboard"))

    if request.args.get("save_chat"):
        return redirect(url_for("dashboard"))

    # Step 3: If the user clicked a past chat from the History tab
    load_id = request.args.get("load_chat_id")
    if load_id:
        session["active_chat_id"] = load_id
        session.modified = True
        _persist_user()
        return redirect(url_for("dashboard"))

    # Step 4: Gather all the data we need to show the Dashboard
    user     = get_current_user()
    u = get_user_record()
    name     = session.get("display_name", user["name"].split()[0])
    settings = session.get("settings", {"default_subject": "Math"})
    answer   = None
    question = ""
    subject  = session.get("active_subject", settings.get("default_subject", "Math"))
    model    = session.get("active_model", settings.get("preferred_model", "groq"))
    error    = None

    is_new_answer = False

    # If the user just submitted a question via the chat box (which sends a POST request)
    if request.method == "POST":
        # Get the question they typed and remove any extra spaces from the ends
        question = request.form.get("question", "").strip()
        if len(question) > 2000:
            error = "Your question is too long. Please keep it under 2000 characters."
        # Get the subject they chose from the dropdown (default to Math)
        subject  = request.form.get("subject", "Math")
        # Get the AI model they chose from the dropdown (default to groq)
        model    = request.form.get("model", "groq")
        
        # Save the chosen subject into their secure session so it stays selected next time
        session["active_subject"] = subject
        # Save the chosen AI model into their secure session
        session["active_model"] = model

        # If the user clicked send but the question box was empty
        if not question:
            # Create an error message to show them on the screen
            error = "Please type a question before clicking Get Help."
        else:

            try:
                # Import the threading library to run the AI request in the background
                import threading as _threading

                # Grab the recent conversation history so the AI remembers what was just said
                current_chat = get_session_active_chat()

                # Build custom API configuration if the user saved their own key in Settings
                custom_cfg = {
                    "use_custom_api": bool(settings.get("use_custom_api")),
                    "provider": settings.get("custom_provider", "claude"),
                    "model": settings.get("custom_model", ""),
                    "api_key": get_saved_custom_api_key(settings),
                }

                # Create a dictionary to hold the AI's answer once it finishes thinking
                _result = {"answer": None}
                # Define a tiny function that will actually talk to the AI API
                def _run():
                    with app.app_context():
                        _result["answer"] = ask_ai(
                            question, subject, model,
                            chat_history=current_chat,
                            custom_config=custom_cfg,
                            user_settings=settings,
                        )
                # Create a background thread to run the AI function so the web server doesn't freeze
                _t = _threading.Thread(target=_run, daemon=True)
                # Start the background thread
                _t.start()
                # Wait up to 60 seconds for the AI to finish answering
                _t.join(timeout=60)

                # If the thread is still running after 60s, or the AI gave us an empty answer
                if _t.is_alive() or not _result["answer"]:
                    # Create a friendly error message for the user instead of breaking the app
                    answer = (
                        "The AI is temporarily unavailable or took too long to respond. "
                        "Please try again in a moment."
                    )
                else:
                    # Otherwise, grab the successful answer from our dictionary
                    answer = _result["answer"]

                # If this is a brand new conversation, generate a unique ID string for it
                if "active_chat_id" not in session:
                    session["active_chat_id"] = str(uuid.uuid4())

                # Friendly label for the model used (e.g. "Claude 3.5 Sonnet (Your Key)")
                used_label = get_model_display_label(model, settings)

                # Get the logged-in user's database record
                u = get_user_record()
                # Respect the user's "Auto-save conversations" setting (defaults to True)
                if u and settings.get("auto_save", True):
                    # Create a new Message object to save the chat to the PostgreSQL database
                    msg = Message(
                        user_id=u.id, # Link it to this specific user
                        chat_id=session["active_chat_id"], # Link it to this specific conversation
                        subject=subject, # Save the subject
                        question=question, # Save what the student asked
                        answer=answer, # Save what the AI answered
                        model_used=used_label if model == "custom" else model, # Save model used
                        is_active=True # Mark the message as visible
                    )
                    # Add the new message to the database queue
                    db.session.add(msg)
                    # Permanently save the queue into the database
                    db.session.commit()
                # Tell Flask that the session data changed and needs to be saved
                session.modified = True
                # Helper function to save any profile updates
                _persist_user()
                # Flag to tell the frontend that we have a new answer to display
                is_new_answer = True

            # If literally anything else crashes in the Python code above
            except Exception as _exc:
                # Print the exact error to the server logs so the developer can debug it
                print(f"ERROR dashboard ask_ai: {_exc}")
                import traceback
                traceback.print_exc()
                answer = (
                    "An error occurred while getting an AI response. "
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
                time_str = _time_ago(msg.created_at)
                
            from flask import jsonify
            return jsonify({
                "question": question,
                "answer": answer,
                "model": get_model_display_label(model, settings) if model == "custom" else _format_model_name(model),
                "time": time_str
            })

    has_custom_api = has_saved_custom_api_key(settings)
    custom_model_label = get_model_display_label("custom", settings) if has_custom_api else ""

    return render_template(
        "dashboard.html",
        user=user, name=name, subjects=SUBJECTS,
        answer=answer, question=question, subject=subject,
        model=model, error=error,
        default_subject=settings.get("default_subject", "Math"),
        groq_enabled=bool(os.getenv("GROQ_API_KEY", "").strip()),
        gemini_enabled=bool(os.getenv("GEMINI_API_KEY", "").strip()),
        has_custom_api=has_custom_api,
        custom_model_label=custom_model_label,
        custom_provider_label=CUSTOM_PROVIDER_CATALOG.get(settings.get("custom_provider", "claude"), {}).get("label", "Custom API"),
        chat_history=get_session_active_chat(),
        is_new_answer=is_new_answer,
    )


# ── History ───────────────────────────────────────────────────────────────────

@app.route("/history")
@login_required
def history():
    """
    This page shows the student a list of all their past chat sessions.
    """
    try:
        # Step 1: Grab the past chats from the database
        try:
            history_data = get_session_history()
        except Exception as db_err:
            print(f"ERROR /history DB: {db_err}")
            history_data = []
            
        # Step 2: Show the History page with their data
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
    """
    This page shows their profile stats (like how many questions they've asked),
    and lets them update their name.
    """
    try:
        user = get_current_user()
        
        # Step 1: If they typed a new name and clicked Save
        if request.method == "POST":
            full_name = request.form.get("first_name", "").strip()
            if full_name:
                session["display_name"] = full_name
                session.modified = True
                try:
                    _persist_user() # Saves to the database
                except Exception as db_err:
                    print(f"ERROR /profile DB save: {db_err}")
                flash("Name updated successfully.")
                return redirect(url_for("profile"))
                
        # Step 2: Grab their chat history so we can count total questions
        try:
            history_data = get_session_history()
        except Exception as db_err:
            print(f"ERROR /profile DB history: {db_err}")
            history_data = []
            
        # Step 3: Show the Profile page
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


# ── Live API Key Verification Endpoint ────────────────────────────────────────

@app.route("/verify_api_key", methods=["POST"])
@login_required
def verify_api_key_route():
    """
    Verifies a user's pasted API key against the chosen provider AND immediately
    encrypts + stores it in the user's server-side PostgreSQL record so the browser
    can wipe the plaintext input from the DOM/console right away.
    """
    data = request.get_json() or {}
    provider = (data.get("provider") or "claude").strip().lower()
    api_key = (data.get("api_key") or "").strip()
    model_name = (data.get("model") or "").strip()

    is_valid, msg, detected_prov = validate_and_verify_api_key(provider, api_key, model_name)
    if not is_valid:
        return jsonify({
            "valid": False,
            "saved": False,
            "provider": detected_prov,
            "message": msg,
            "masked": "",
        }), 400

    # Ensure model_name belongs to detected_prov; if not, pick the first catalog model for that provider
    prov_models = CUSTOM_PROVIDER_CATALOG.get(detected_prov, {}).get("models", [])
    valid_model_ids = [m["id"] for m in prov_models]
    if not model_name or model_name not in valid_model_ids:
        model_name = valid_model_ids[0] if valid_model_ids else model_name

    settings = session.get("settings", {"default_subject": "Math"})
    settings["custom_provider"] = detected_prov
    settings["custom_model"] = model_name
    settings["use_custom_api"] = True
    settings["preferred_model"] = "custom"

    # Encrypt and store strictly on the server-side user record; strip from browser cookie
    save_user_encrypted_api_key(api_key, settings)

    session["settings"] = settings
    session["active_model"] = "custom"
    session.modified = True
    _persist_user()

    return jsonify({
        "valid": True,
        "saved": True,
        "provider": detected_prov,
        "model": model_name,
        "message": msg,
        "masked": mask_api_key(api_key),
        "model_label": get_model_display_label("custom", settings),
    }), 200


# ── Export User Data (JSON Download) ──────────────────────────────────────────

def _export_history():
    u = get_user_record()
    if not u:
        return []
    msgs = Message.query.filter_by(user_id=u.id).order_by(Message.created_at.asc()).all()
    return [{
        "chat_id": m.chat_id,
        "subject": m.subject,
        "question": m.question,
        "answer": m.answer,
        "model": _format_model_name(m.model_used),
        "created_at": m.created_at.isoformat() + "Z" if m.created_at else None,
    } for m in msgs]


@app.route("/export_data")
@login_required
def export_data():
    """Exports the logged-in student's profile & study history as a clean JSON file (never includes API keys)."""
    import json as _json
    user = get_current_user()
    safe_settings = dict(session.get("settings", {}))
    safe_settings.pop("custom_api_key", None)
    safe_settings.pop("custom_api_key_enc", None)
    payload = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "student": {
            "name": session.get("display_name", user.get("name", "Student")),
            "email": user.get("email", ""),
        },
        "preferences": safe_settings,
        "history": _export_history(),
    }
    resp = app.response_class(
        response=_json.dumps(payload, indent=2),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Content-Disposition"] = "attachment; filename=ai-student-helper-data.json"
    return resp


# ── Settings ──────────────────────────────────────────────────────────────────

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """
    This page lets the user change their preferences (dark mode, default subject, etc.)
    and also lets them clear their chat history permanently.
    """
    user     = get_current_user()
    settings = session.get("settings", {"default_subject": "Math"})

    # Ensure any legacy plaintext or cookie-stored key is migrated to server-side DB & scrubbed from cookie
    if settings.get("custom_api_key") or settings.get("custom_api_key_enc"):
        legacy_raw = get_saved_custom_api_key(settings) or decrypt_api_key(settings.get("custom_api_key", ""))
        settings.pop("custom_api_key", None)
        settings.pop("custom_api_key_enc", None)
        if legacy_raw:
            save_user_encrypted_api_key(legacy_raw, settings)
        session["settings"] = settings
        session.modified = True

    if request.method == "POST":
        # Step 1: Did they click the "Clear Chat History" button?
        if request.form.get("clear_history"):
            u = get_user_record()
            if u:
                Message.query.filter_by(user_id=u.id).delete()
                db.session.commit()
                _persist_user()
                flash("History cleared.")
        else:
            # Step 2: They clicked "Save Settings", so we grab everything from the form
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
            settings["grade_level"]      = request.form.get("grade_level", "high_school")
            settings["ai_tone"]          = request.form.get("ai_tone", "step_by_step")
            settings["include_practice"] = bool(request.form.get("include_practice"))
            settings["show_timestamps"]  = bool(request.form.get("show_timestamps"))

            # Step 2b: Custom API key & provider fields (BYOK) — validated & encrypted per user
            settings["use_custom_api"]   = bool(request.form.get("use_custom_api"))
            if "custom_provider" in request.form:
                settings["custom_provider"] = request.form.get("custom_provider", "claude").strip().lower()
            if "custom_model" in request.form:
                settings["custom_model"] = request.form.get("custom_model", "").strip()

            if request.form.get("clear_custom_api_key") == "1":
                save_user_encrypted_api_key("", settings)
                settings["use_custom_api"] = False
                if settings["preferred_model"] == "custom":
                    settings["preferred_model"] = "groq"
                session["settings"] = settings
                session["active_model"] = settings["preferred_model"]
                session.modified = True
                _persist_user()
                flash("Removed your custom API key and switched back to built-in models.")
                return redirect(url_for("settings"))

            submitted_key = request.form.get("custom_api_key", "").strip()
            if submitted_key:
                # Validate format and verify live with the AI provider before saving
                is_valid, verify_msg, detected_prov = validate_and_verify_api_key(
                    settings.get("custom_provider", "claude"),
                    submitted_key,
                    settings.get("custom_model", ""),
                )
                if not is_valid:
                    session["settings"] = settings
                    session.modified = True
                    flash(f"Error: {verify_msg}")
                    return redirect(url_for("settings"))

                settings["custom_provider"] = detected_prov
                prov_models = CUSTOM_PROVIDER_CATALOG.get(detected_prov, {}).get("models", [])
                valid_ids = [m["id"] for m in prov_models]
                if not settings.get("custom_model") or settings["custom_model"] not in valid_ids:
                    if valid_ids:
                        settings["custom_model"] = valid_ids[0]

                # Encrypt key at rest in user's DB record and never store plaintext in session cookie
                save_user_encrypted_api_key(submitted_key, settings)
                settings["use_custom_api"] = True

            # Sync has_custom_api status from server-side DB
            has_key = has_saved_custom_api_key(settings)
            settings["has_custom_api"] = has_key
            settings["custom_key_masked"] = get_masked_custom_api_key(settings) if has_key else ""

            # If user toggled "Use my own API key" on and has a valid encrypted key saved, make "custom" active
            if settings.get("use_custom_api") and has_key:
                settings["preferred_model"] = "custom"
            elif settings.get("preferred_model") == "custom" and not has_key:
                settings["preferred_model"] = "groq"
                settings["use_custom_api"] = False

            session["settings"] = settings
            
            # Step 3: Keep everything synchronized and save to database
            session["active_subject"] = settings["default_subject"]
            session["active_model"]   = settings["preferred_model"]
            
            session.modified = True
            _persist_user()
            flash("Settings saved.")
        return redirect(url_for("settings"))

    has_key = has_saved_custom_api_key(settings)
    masked_key = get_masked_custom_api_key(settings) if has_key else ""

    # Step 4: Show the Settings page
    return render_template(
        "settings.html",
        user=user,
        name=session.get("display_name", user["name"]),
        subjects=SUBJECTS,
        settings=settings,
        groq_enabled=bool(os.getenv("GROQ_API_KEY", "").strip()),
        gemini_enabled=bool(os.getenv("GEMINI_API_KEY", "").strip()),
        provider_catalog=CUSTOM_PROVIDER_CATALOG,
        has_custom_api=has_key,
        custom_key_masked=masked_key,
        custom_model_label=get_model_display_label("custom", settings),
    )


# ── About ─────────────────────────────────────────────────────────────────────

@app.route("/about")
def about():
    try:
        from urllib.parse import urlparse
        u_rec = get_user_record()
        from_public = request.args.get("from") == "public"
        needs_setup = bool(session.get("needs_setup"))
        ref_path = urlparse(request.referrer or "").path
        from_onboarding_ref = ref_path in ("/", "/setup", "/signin", "/signup")
        show_sidebar_user = get_current_user() if (u_rec and not from_public and not needs_setup and not from_onboarding_ref) else None
        return render_template("about.html", user=show_sidebar_user)
    except Exception as e:
        print(f"ERROR /about: {e}")
        return render_template("about.html", user=None)


# ── Privacy Policy & Terms ────────────────────────────────────────────────────

@app.route("/privacy")
def privacy():
    try:
        from urllib.parse import urlparse
        u_rec = get_user_record()
        from_public = request.args.get("from") == "public"
        needs_setup = bool(session.get("needs_setup"))
        ref_path = urlparse(request.referrer or "").path
        from_onboarding_ref = ref_path in ("/", "/setup", "/signin", "/signup")
        show_sidebar_user = get_current_user() if (u_rec and not from_public and not needs_setup and not from_onboarding_ref) else None
        return render_template("privacy.html", user=show_sidebar_user)
    except Exception as e:
        print(f"ERROR /privacy: {e}")
        return render_template("privacy.html", user=None)


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
    """
    Saves the user's current session data (name, settings) directly into the database
    while preserving their server-side encrypted API key (`custom_api_key_enc`) and keeping
    all secret material out of the browser session cookie.
    """
    u = get_user_record()
    if u:
        existing_db_settings = dict(u.settings) if isinstance(u.settings, dict) else {}
        saved_enc = existing_db_settings.get("custom_api_key_enc", "")

        sess_settings = dict(session.get("settings", {"default_subject": "Math"}))
        # Never store raw or encrypted API key in the client-side browser cookie
        sess_settings.pop("custom_api_key", None)
        sess_settings.pop("custom_api_key_enc", None)
        session["settings"] = sess_settings

        merged = dict(sess_settings)
        if saved_enc:
            merged["custom_api_key_enc"] = saved_enc
        u.settings = merged

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
    if request.path in ("/favicon.ico", "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png"):
        return "", 204
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
       "application/json" in request.headers.get("Accept", ""):
        return jsonify({"error": "Page not found."}), 404
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

if __name__ == "__main__":
    app.run(debug=True, port=5001)
