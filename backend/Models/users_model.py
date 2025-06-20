# /backend/Models/users_model.py
from backend.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo 
from backend.Models.rbac_model import user_roles

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_password = db.Column(db.String(255), nullable=False)
    user_email = db.Column(db.String(100), unique=True, nullable=False)
    user_phone_num = db.Column(db.String(10))
    user_status = db.Column(db.Boolean, nullable=False, default=True)
    user_avatar = db.Column(db.String(255), nullable=True)
    user_reset_token = db.Column(db.String(128), nullable=True)
    user_reset_expire_at = db.Column(db.DateTime(timezone=True), nullable=True)
    user_create_at = db.Column(db.DateTime(timezone=True),
                           nullable=False,
                           default=lambda: datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')))

    # quan hệ many-to-many tới Role
    roles = db.relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="joined",
    )
    devices = db.relationship(
        "Device",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    # ---- tiện ích: lấy nhanh toàn bộ permission của user ----
    @property
    def permissions(self) -> set[str]:
        """Tập các tên quyền (perm_name) mà user này sở hữu thông qua các role."""
        perms = {p.perm_name for role in self.roles for p in role.permissions}
        return perms

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.user_id} - {self.user_email}>"