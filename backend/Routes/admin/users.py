# backend/Routes/admin/users.py
from flask import Blueprint, jsonify
from backend.Models.users_model import User
from backend.decorators.auth_decorators import admin_required

bp = Blueprint("admin_users", __name__, url_prefix="/api/admin/users")

@bp.route("/", methods=["GET"])
@admin_required
def get_all_users():
    users = User.query.order_by(User.user_create_at.desc()).all()
    data = [
        {
            "id": user.user_id,
            "name": user.user_name,
            "email": user.user_email,
            "phone": user.user_phone_num,
            "status": user.user_status,
            "created_at": user.user_create_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for user in users
    ]
    return jsonify({"success": True, "data": data})
