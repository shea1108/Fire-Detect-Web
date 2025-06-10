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