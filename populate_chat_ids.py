from app import app, db, Message
import uuid

with app.app_context():
    try:
        messages = Message.query.filter_by(chat_id=None).all()
        for m in messages:
            m.chat_id = str(uuid.uuid4())
        db.session.commit()
        print(f"Updated {len(messages)} old messages with unique chat_ids.")
    except Exception as e:
        print(f"Error: {e}")
