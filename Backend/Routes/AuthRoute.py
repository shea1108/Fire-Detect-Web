from flask import Blueprint, request
from Backend.controllers.auth_controller import register_user, login_user

auth_bp = Blueprint('auth', __name__)

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        return register_user(request.json)
    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"error": "Lỗi máy chủ"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    return login_user(data)
