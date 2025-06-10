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

    data = request.json or request.form

    user_name = data.get('user_name')
    user_phone_num = data.get('user_phone_num')
    user_email = data.get('user_email')

    if user_phone_num:
        if not user_phone_num.isdigit() or len(user_phone_num) != 10:
            return jsonify({'error': 'Số điện thoại phải gồm 10 chữ số'}), 400
        existing_phone = User.query.filter(
            User.user_phone_num == user_phone_num,
            User.user_id != user_id
        ).first()
        if existing_phone:
            return jsonify({'error': 'Số điện thoại đã được đăng ký'}), 400

    if user_email and user_email != user.user_email:
        existing_email = User.query.filter(
            User.user_email == user_email,
            User.user_id != user_id
        ).first()
        if existing_email:
            return jsonify({'error': 'Email đã được đăng ký'}), 400
        user.user_email = user_email

    if user_name:
        user.user_name = user_name
    if user_phone_num:
        user.user_phone_num = user_phone_num

    db.session.commit()

    # Cập nhật session
    session['user_name'] = user.user_name
    session['user_phone_num'] = user.user_phone_num
    session['user_email'] = user.user_email
    session.modified = True

    return jsonify({
        'message': 'Đăng nhập thành công',
        'user_id': user.user_id,
        'user_name': user.user_name,
        'user_email': user.user_email,
        'user_phone_num': user.user_phone_num,
        'role': user.user_role
    }), 200

