from backend.extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_password = db.Column(db.String(255), nullable=False)
    user_role = db.Column(db.String(20), nullable=False)
    user_email = db.Column(db.String(100), unique=True, nullable=False)
    user_phone_num = db.Column(db.String(10))
    user_status = db.Column(db.Boolean, nullable=False, default=True)
    user_create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
