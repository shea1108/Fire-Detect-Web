from backend.extensions import db
from datetime import datetime
import uuid

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_name = db.Column(db.String(100), nullable=False)
    user_password = db.Column(db.String(255), nullable=False)
    user_role = db.Column(db.String(20), nullable=False)
    user_email = db.Column(db.String(100), unique=True, nullable=False)
    user_phone_num = db.Column(db.String(10))
    user_status = db.Column(db.Boolean, nullable=False, default=True)
    user_create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
