from backend.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo 

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_password = db.Column(db.String(255), nullable=False)
    user_role = db.Column(db.String(20), nullable=False)
    user_email = db.Column(db.String(100), unique=True, nullable=False)
    user_phone_num = db.Column(db.String(10))
    user_status = db.Column(db.Boolean, nullable=False, default=True)
    user_avatar = db.Column(db.String(255), nullable=True)
    user_reset_token = db.Column(db.String(128), nullable=True)
    user_reset_expire_at = db.Column(db.DateTime(timezone=True), nullable=True)
    user_create_at = db.Column(db.DateTime(timezone=True),
                           nullable=False,
                           default=lambda: datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')))
