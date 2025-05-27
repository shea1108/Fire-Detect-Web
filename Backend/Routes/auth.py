##### backend/routes/auth.py
from flask import Blueprint, request, jsonify
from backend.Controllers.auth_controller import register_user, login_user

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    try:
        return register_user(request.json)
    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"error": "Lỗi máy chủ"}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        return login_user(request.json)
    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"error": "Lỗi máy chủ"}), 500