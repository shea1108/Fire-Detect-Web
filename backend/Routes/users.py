# routes/user.py
from backend.Models.users_model import User
from flask import Blueprint,request, jsonify
from backend.Controllers.user_controller import (
    edit_user_profile,
    recover_password,
    submit_reset_password        # <— mới
)

bp = Blueprint('user_check', __name__, url_prefix='/api/user')

@bp.route('/check-email-exists', methods=['POST'])
def check_email_exists():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'exists': False, 'error': 'Thiếu email'}), 400

    user = User.query.filter_by(user_email=email).first()
    return jsonify({'exists': user is not None})



# Route cập nhật hồ sơ người dùng (POST /api/user/edit)
@bp.route('/edit', methods=['POST'])
def api_edit_user():
    return edit_user_profile()

# Route khôi phục mật khẩu (POST /api/user/recover-password)
@bp.route('/recover-password', methods=['POST'])
def api_recover_password():
    return recover_password()





# ĐẶT LẠI MẬT KHẨU (AJAX POST)
@bp.route('/reset-password/<token>', methods=['POST'])
def api_submit_reset_password(token):
    return submit_reset_password(token)