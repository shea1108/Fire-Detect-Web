from backend.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo 


class Notification(db.Model):
    __tablename__ = 'notifications'

    noti_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    log_id = db.Column(db.Integer, db.ForeignKey('logs.log_id', ondelete='CASCADE', onupdate='CASCADE'))
    noti_title = db.Column(db.String(100), nullable=False)
    noti_message = db.Column(db.Text, nullable=False)
    noti_is_receive = db.Column(db.Boolean, nullable=False, default=False)
    noti_create_at =  db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")))

    notification_platforms = db.relationship('NotificationPlatform', backref='notification', lazy=True, cascade="all, delete-orphan")
