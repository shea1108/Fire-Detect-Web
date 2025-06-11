from flask import Blueprint, request, jsonify, session
from backend.Models.users_model import User
from backend.extensions import db

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/edit', methods=['POST'])
def edit_user_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or request.form

    new_name = data.get('user_name')
    new_phone = data.get('user_phone_num')
    new_email = data.get('user_email')

    # Kiểm tra số điện thoại
    if new_phone:
        if not new_phone.isdigit() or len(new_phone) != 10:
            return jsonify({'error': 'Số điện thoại phải gồm 10 chữ số'}), 400
        existing_phone = User.query.filter(
            User.user_phone_num == new_phone,
            User.user_id != user_id
        ).first()
        if existing_phone:
            return jsonify({'error': 'Số điện thoại đã được đăng ký'}), 400
        user.user_phone_num = new_phone  # luôn gán khi hợp lệ

    # Kiểm tra và gán email
    if new_email:
        existing_email = User.query.filter(
            User.user_email == new_email,
            User.user_id != user_id
        ).first()
        if existing_email:
            return jsonify({'error': 'Email đã được đăng ký'}), 400
        user.user_email = new_email  # gán luôn, kể cả giống cũ

    # Gán tên (nếu có)
    if new_name:
        user.user_name = new_name

    try:
        db.session.flush()  # để bắt lỗi unique nếu có trước khi commit
        db.session.commit()

        # Cập nhật lại session
        session['user_name'] = user.user_name
        session['user_phone_num'] = user.user_phone_num
        session['user_email'] = user.user_email
        session.modified = True

        return jsonify({
            'message': 'Cập nhật thành công',
            'user_id': user.user_id,
            'user_name': user.user_name,
            'user_email': user.user_email,
            'user_phone_num': user.user_phone_num,
            'role': user.user_role
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Lỗi khi cập nhật profile: {e}")
        return jsonify({'error': 'Lỗi hệ thống'}), 500
