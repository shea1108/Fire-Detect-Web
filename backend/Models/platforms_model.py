from backend.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo 
class Platform(db.Model):
    __tablename__ = 'platforms'

    plat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plat_name = db.Column(db.String(100), nullable=False)
    plat_endpoint = db.Column(db.Text)
    plat_create_at =  db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")))

    user_platforms = db.relationship('UserPlatform', backref='platform', lazy=True, cascade="all, delete-orphan")
    notification_platforms = db.relationship('NotificationPlatform', backref='platform', lazy=True, cascade="all, delete-orphan")
