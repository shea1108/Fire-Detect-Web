##### backend/routes/auth.py
from flask import Blueprint, request, jsonify
from backend.Controllers.auth_controller import register_user, login_user
from flask import session


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
    

@bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' in session:
        return jsonify({
            'user_id': session['user_id'],
            'user_email': session['user_email'],
            'role': session['user_role']
        }), 200
    return jsonify({'error': 'Chưa đăng nhập'}), 401



@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Đăng xuất thành công'}), 200
