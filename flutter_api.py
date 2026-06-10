import uuid
from flask import Blueprint, request, jsonify

flutter_bp = Blueprint('flutter_bp', __name__)

@flutter_bp.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, DELETE, PUT'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@flutter_bp.route("/api/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    return "", 200

import sys

def get_app_module():
    if "app" in sys.modules and getattr(sys.modules["app"], "db", None) is not None:
        return sys.modules["app"]
    return sys.modules["__main__"]

def get_user_from_token():
    User = get_app_module().User
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    return User.query.filter_by(session_token=token).first()

@flutter_bp.route("/api/signup", methods=["POST"])
def api_signup():
    app_mod = get_app_module()
    db = app_mod.db
    User = app_mod.User
    data = request.get_json() or {}
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password or not first_name:
        return jsonify({"error": "Missing required fields"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400

    session_token = uuid.uuid4().hex
    new_user = User(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        default_subject="Math",
        settings={"default_subject": "Math"},
        session_token=session_token
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"token": session_token, "user": {"name": f"{first_name} {last_name}".strip(), "email": email}})

@flutter_bp.route("/api/google-signin", methods=["POST"])
def api_google_signin():
    data = request.get_json() or {}
    id_token = data.get("id_token")
    if not id_token:
        return jsonify({"error": "Missing id_token"}), 400
        
    try:
        import requests as req
        resp = req.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
        if not resp.ok:
            return jsonify({"error": "Invalid token from Google"}), 401
            
        info = resp.json()
        google_id = info.get("sub")
        email = info.get("email")
        name = info.get("name")
        
        if not google_id or not email:
            return jsonify({"error": "Incomplete token info"}), 401
            
        User = get_app_module().User
        db = get_app_module().db
        
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            if not user.session_token:
                import uuid
                user.session_token = uuid.uuid4().hex
            db.session.commit()
        else:
            first_name = info.get("given_name", "")
            last_name = info.get("family_name", "")
            if not first_name and name:
                first_name = name.split()[0]
            import uuid
            user = User(
                google_id=google_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                default_subject="Math",
                settings={"default_subject": "Math"},
                session_token=uuid.uuid4().hex
            )
            db.session.add(user)
            db.session.commit()
            
        return jsonify({"token": user.session_token, "user": {"email": email, "name": name}})
    except Exception as e:
        print(f"ERROR /api/google-signin: {e}")
        return jsonify({"error": "Internal server error"}), 500

@flutter_bp.route("/api/signin", methods=["POST"])
@flutter_bp.route("/api/login", methods=["POST"])
def api_signin():
    app_mod = get_app_module()
    db = app_mod.db
    User = app_mod.User
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or user.password != password:
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.session_token:
        user.session_token = uuid.uuid4().hex
        db.session.commit()

    return jsonify({"token": user.session_token, "user": {"name": f"{user.first_name} {user.last_name}".strip(), "email": email}})

@flutter_bp.route("/api/ask", methods=["POST"])
def api_ask():
    app_mod = get_app_module()
    db = app_mod.db
    Message = app_mod.Message
    ask_ai = app_mod.ask_ai
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    subject = data.get("subject", "Math")
    model = data.get("model", "groq")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    # Get active chat history
    active_chat_id = data.get("chat_id")
    if active_chat_id:
        msgs = Message.query.filter_by(user_id=user.id, chat_id=active_chat_id).order_by(Message.created_at.asc()).all()
    else:
        active_chat_id = uuid.uuid4().hex
        msgs = []

    chat_history = [{"question": m.question, "answer": m.answer} for m in msgs]

    answer = ask_ai(question, subject, model, chat_history=chat_history)

    msg = Message(
        user_id=user.id,
        chat_id=active_chat_id,
        subject=subject,
        question=question,
        answer=answer,
        model_used=model,
        is_active=True
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        "answer": answer,
        "chat_id": active_chat_id,
        "time": msg.created_at.strftime("%b %d, %Y %I:%M %p") if msg.created_at else "Just now"
    })

@flutter_bp.route("/api/history", methods=["GET"])
def api_history():
    Message = get_app_module().Message
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    msgs = Message.query.filter_by(user_id=user.id).order_by(Message.created_at.desc()).all()
    
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
            
    return jsonify({"history": chats})

@flutter_bp.route("/api/user", methods=["GET"])
def api_user():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "settings": user.settings
    })

@flutter_bp.route("/api/settings", methods=["POST"])
def api_settings():
    db = get_app_module().db
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    settings = user.settings or {}
    
    if "default_subject" in data:
        settings["default_subject"] = data["default_subject"]
        user.default_subject = data["default_subject"]
        
    if "first_name" in data and data["first_name"]:
        user.first_name = data["first_name"]
        
    if "last_name" in data and data["last_name"]:
        user.last_name = data["last_name"]
    
    user.settings = settings
    db.session.commit()
    
    return jsonify({"status": "success", "settings": user.settings})

@flutter_bp.route("/api/history", methods=["DELETE"])
def api_delete_history():
    app_mod = get_app_module()
    db = app_mod.db
    Message = app_mod.Message
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    Message.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    
    return jsonify({"status": "success", "message": "History cleared"})
