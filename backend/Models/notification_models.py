from backend.extensions import db

class NotificationPlatform(db.Model):
    __tablename__ = 'notification_platforms'

    noti_id = db.Column(db.Integer, db.ForeignKey('notifications.noti_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    plat_id = db.Column(db.Integer, db.ForeignKey('platforms.plat_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    np_status = db.Column(db.Boolean)
    np_sent_at = db.Column(db.DateTime)
    np_error_message = db.Column(db.Text)
    np_retry_count = db.Column(db.Integer, default=0)
    np_payload = db.Column(db.Text)
    np_recipient_address = db.Column(db.String(255))
    np_response_data = db.Column(db.Text)
