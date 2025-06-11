from flask import Blueprint, request, jsonify, session
from backend.Models.users_model import User
from backend.extensions import db
from backend.utils.auth_utils import login_required_redirect 

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/edit', methods=['POST'])
def edit_user_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400

    new_name = data.get('user_name')
    new_phone = data.get('user_phone_num')

    if new_name:
        user.user_name = new_name

    if new_phone:

        existing_user = User.query.filter(User.user_phone_num == new_phone, User.user_id != user_id).first()
        if existing_user:
            return jsonify({'error': 'Phone number already registered'}), 409 # Conflict

        user.user_phone_num = new_phone

    try:
        db.session.commit()
        session['user_name'] = user.user_name
        return jsonify({'message': 'Cập nhật thành công'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating profile: {e}")
        return jsonify({'error': 'Database error'}), 500
    


@user_bp.route('/recover-password', methods=['POST'])
def recover_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({'success': False, 'message': 'Thiếu email'}), 400

    user = User.query.filter_by(user_email=email).first()
    if not user:
        return jsonify({'success': True, 'message': 'Nếu email tồn tại, bạn sẽ nhận được hướng dẫn'}), 200

    # Tạo token
    from backend.utils.token_utils import generate_reset_token
    token = generate_reset_token(email)
    reset_link = f"http://localhost:5000/reset-password/{token}"

    # Gửi mail
    from backend.Controllers.mail_controller import send_email
    subject = "🔐 Đặt lại mật khẩu tài khoản FireDetect"
    html_body = f"""
        <h3>Yêu cầu đặt lại mật khẩu</h3>
        <p>Nhấn vào liên kết dưới đây để đặt lại mật khẩu. Liên kết này chỉ có hiệu lực trong 5 phút:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>Nếu bạn không yêu cầu, hãy bỏ qua email này.</p>
    """
    send_email(subject, html_body, email)
    return jsonify({'success': True, 'message': 'Nếu email tồn tại, bạn sẽ nhận được hướng dẫn'}), 200
