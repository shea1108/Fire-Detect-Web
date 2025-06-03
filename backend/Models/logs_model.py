# models.py
from datetime import datetime
from backend.extensions import db


class Log(db.Model):
    __tablename__ = 'logs'
    log_id = db.Column(db.String(50), primary_key=True)
    dev_id = db.Column(db.String(50), db.ForeignKey('devices.dev_id', ondelete="CASCADE", onupdate="CASCADE"))
    model_id = db.Column(db.String(50), db.ForeignKey('models.model_id', ondelete="CASCADE", onupdate="CASCADE"))
    log_fire_confidence = db.Column(db.Float, nullable=True)
    log_image_path = db.Column(db.String(255), nullable=True)
    log_create_at = db.Column(db.DateTime, default=datetime.utcnow)
