from app import app, db
from sqlalchemy import text

with app.app_context():
    # Execute the raw SQL migration
    try:
        db.session.execute(text("ALTER TABLE message ADD COLUMN chat_id VARCHAR(36);"))
        db.session.commit()
        print("Migration successful: Added chat_id to message table.")
    except Exception as e:
        print(f"Migration error or already exists: {e}")
