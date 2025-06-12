# backend/Models/rbac_model.py
from backend.extensions import db


# -------------------------
#  ASSOCIATION (JOIN) TABLE
# -------------------------

# nhiều user – nhiều role
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.user_id",
                                                   ondelete="CASCADE"),
              primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.role_id",
                                                   ondelete="CASCADE"),
              primary_key=True),
)

# nhiều role – nhiều permission
role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.role_id",
                                                   ondelete="CASCADE"),
              primary_key=True),
    db.Column("perm_id", db.Integer, db.ForeignKey("permissions.perm_id",
                                                   ondelete="CASCADE"),
              primary_key=True),
)


# -------------
#  CORE MODELS
# -------------


class Role(db.Model):
    __tablename__ = "roles"

    role_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)

    users = db.relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        lazy="joined",
    )
    permissions = db.relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="joined",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role {self.role_name}>"


class Permission(db.Model):
    __tablename__ = "permissions"

    perm_id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    perm_name        = db.Column(db.String(100), unique=True, nullable=False)
    perm_description = db.Column(db.Text)

    roles = db.relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="joined",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Perm {self.perm_name}>"
