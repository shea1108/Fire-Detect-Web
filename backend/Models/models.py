from backend.extensions import db
from datetime import datetime

class Model(db.Model):
    __tablename__ = 'models'

    model_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_path = db.Column(db.Text, nullable=False)
    model_config = db.Column(db.Text)
    model_status = db.Column(db.Boolean, nullable=False, default=True)
    model_create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    logs = db.relationship('Log', backref='model', lazy=True, cascade="all, delete-orphan")
