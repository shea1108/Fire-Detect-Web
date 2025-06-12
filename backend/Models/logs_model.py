# models.py
from datetime import datetime
from backend.extensions import db


class Log(db.Model):
    __tablename__ = 'logs'
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dev_id = db.Column(db.Integer, db.ForeignKey('devices.dev_id', ondelete="CASCADE", onupdate="CASCADE"))
    model_id = db.Column(db.Integer, db.ForeignKey('models.model_id', ondelete="CASCADE", onupdate="CASCADE"))
    
    log_image_path = db.Column(db.String(255), nullable=True)
    log_create_at = db.Column(db.DateTime, default=datetime.utcnow)
    bboxes = db.relationship('LogBBox', backref='log', lazy=True, cascade="all, delete-orphan")
    def __repr__(self):
        return f'<Log {self.log_id}>'