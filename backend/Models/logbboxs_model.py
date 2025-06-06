from backend.extensions import db

class LogBbox(db.Model):
    __tablename__ = 'log_bboxes'
    bbox_id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey('logs.log_id', ondelete='CASCADE'), nullable=False)
    confidence = db.Column(db.Float, db.CheckConstraint('confidence BETWEEN 0 AND 1'))
    x_center = db.Column(db.Float)
    y_center = db.Column(db.Float)
    width = db.Column(db.Float)
    height = db.Column(db.Float)

    def __repr__(self):
        return f'<LogBbox {self.bbox_id}>'