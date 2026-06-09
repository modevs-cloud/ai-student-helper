import uuid
from flask import Blueprint, request, jsonify

flutter_bp = Blueprint('flutter_bp', __name__)

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
