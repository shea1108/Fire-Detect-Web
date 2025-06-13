
from backend.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo 
class Model(db.Model):
    __tablename__ = 'models'

    model_id = db.Column(db.String(50), primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_path = db.Column(db.Text, nullable=False)
    model_config = db.Column(db.Text)
    model_status = db.Column(db.Boolean, nullable=False)
    model_create_at =  db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")))

    logs = db.relationship("Log", backref="model", lazy=True)
