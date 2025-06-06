from backend.Models.users_model import User
from backend.extensions import db, bcrypt  
from flask import jsonify, session



def register_user(data):
    email = data.get('user_email')
    password = data.get('user_password')
    name = data.get('user_name')
    phone = data.get('user_phone_num', '')
    role = data.get('user_role', 'user')

    if not all([email, password, name, role]):
        return jsonify({'error': 'Thiếu thông tin'}), 400

    if User.query.filter_by(user_email=email).first():
        return jsonify({'error': 'Email đã tồn tại'}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(
        user_email=email,
        user_password=hashed_pw,
        user_name=name,
        user_phone_num=phone,
        user_role=role
    )

    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Đăng ký thành công'}), 201

def login_user(data):
    email = data.get('user_email')
    password = data.get('user_password')

    if not all([email, password]):
        return jsonify({'error': 'Thiếu thông tin'}), 400

    user = User.query.filter_by(user_email=email).first()
    if user and bcrypt.check_password_hash(user.user_password, password):
        # Lưu vào session
        session['user_id'] = user.user_id
        session['user_name'] = user.user_name
        session['user_email'] = user.user_email
        session['user_role'] = user.user_role
        session.permanent = True
        return jsonify({
            'message': 'Đăng nhập thành công',
            'user_id': user.user_id,
            'role': user.user_role
        }), 200
    else:
        return jsonify({'error': 'Email hoặc mật khẩu không đúng'}), 401
