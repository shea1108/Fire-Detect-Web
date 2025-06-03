from backend.extensions import db
from datetime import datetime

class Device(db.Model):
    __tablename__ = 'devices'

    dev_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'))
    dev_name = db.Column(db.String(100), nullable=False)
    dev_location = db.Column(db.String(255))
    dev_ip_address = db.Column(db.String(50))
    dev_status = db.Column(db.Boolean, nullable=False, default=True)
    dev_create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    logs = db.relationship('Log', backref='device', lazy=True, cascade="all, delete-orphan")
