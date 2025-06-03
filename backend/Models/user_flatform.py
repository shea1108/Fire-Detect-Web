from backend.extensions import db

class UserPlatform(db.Model):
    __tablename__ = 'user_platforms'

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    plat_id = db.Column(db.Integer, db.ForeignKey('platforms.plat_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
