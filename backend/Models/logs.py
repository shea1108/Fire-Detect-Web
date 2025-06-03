from backend.extensions import db
from datetime import datetime

class Log(db.Model):
    __tablename__ = 'logs'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dev_id = db.Column(db.Integer, db.ForeignKey('devices.dev_id', ondelete='CASCADE', onupdate='CASCADE'))
    model_id = db.Column(db.Integer, db.ForeignKey('models.model_id', ondelete='CASCADE', onupdate='CASCADE'))
    log_fire_confidence = db.Column(db.Float, nullable=True)
    log_image_path = db.Column(db.String(255))
    log_create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    notifications = db.relationship('Notification', backref='log', lazy=True, cascade="all, delete-orphan")
