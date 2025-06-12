import os
import random
import string
from datetime import datetime, timedelta
import secrets


from flask import Blueprint, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from authlib.integrations.base_client.errors import OAuthError


from backend.Models.users_model import User, db
from backend.extensions import oauth, mail

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def send_otp_email(recipient_email, otp):
    try:
        msg = Message(
            subject="Mã Xác Thực Đăng Ký Tài Khoản",
            recipients=[recipient_email],
            body=f"Mã OTP của bạn là: {otp}\n\nMã này sẽ hết hạn trong 5 phút."
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")
        return False


@bp.route('/register/send-otp', methods=['POST'])
def register_send_otp():

    data = request.json
    user_name = data.get('user_name')
    user_email = data.get('user_email')
    user_password = data.get('user_password')
    user_phone_num = data.get('user_phone_num')
    user_role = data.get('user_role')

    if not all([user_name, user_email, user_password, user_role]):
        return jsonify({"error": "Vui lòng điền đầy đủ các trường bắt buộc."}), 400

    existing_user = User.query.filter_by(user_email=user_email, user_status=True).first()
    if existing_user:
        return jsonify({"error": "Email này đã được sử dụng."}), 409

    otp = "".join(random.choices(string.digits, k=6))
    hashed_password = generate_password_hash(user_password)

    if not send_otp_email(user_email, otp):
        return jsonify({"error": "Không thể gửi email xác thực. Vui lòng thử lại."}), 500

    session['registration_data'] = {
        'user_name': user_name,
        'user_email': user_email,
        'user_password': hashed_password,
        'user_phone_num': user_phone_num,
        'user_role': user_role,
        'otp': otp,
        'expiry': (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    }
    session.permanent = True

    return jsonify({"message": "Mã OTP đã được gửi đến email của bạn.", "email": user_email}), 200


@bp.route('/register/verify-otp', methods=['POST'])
def register_verify_otp():
    data = request.json
    user_email = data.get('email')
    submitted_otp = data.get('otp')

    reg_data = session.get('registration_data')

    if not reg_data or reg_data.get('user_email') != user_email:
        return jsonify({"error": "Phiên đăng ký không hợp lệ hoặc đã hết hạn."}), 400
    
    if reg_data.get('otp') != submitted_otp:
        return jsonify({"error": "Mã OTP không chính xác."}), 400

    try:
        expiry_time = datetime.fromisoformat(reg_data.get('expiry'))
        if datetime.utcnow() > expiry_time:
            session.pop('registration_data', None)
            return jsonify({"error": "Mã OTP đã hết hạn."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Dữ liệu hết hạn không hợp lệ."}), 400


    new_user = User(
        user_name=reg_data['user_name'],
        user_email=reg_data['user_email'],
        user_password=reg_data['user_password'],
        user_phone_num=reg_data.get('user_phone_num'),
        user_role=reg_data['user_role'],
        user_status=True
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        session.pop('registration_data', None)
        return jsonify({"message": "Đăng ký tài khoản thành công!"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi tạo user: {e}")
        return jsonify({"error": "Lỗi khi tạo tài khoản trong cơ sở dữ liệu."}), 500


@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user_email = data.get('user_email')
    user_password = data.get('user_password')

    user = User.query.filter_by(user_email=user_email, user_status=True).first()

    # Kiểm tra user tồn tại và mật khẩu khớp
    if user and user.user_password and check_password_hash(user.user_password, user_password):
        session['user_id'] = user.user_id
        session['user_name'] = user.user_name
        session['user_email'] = user.user_email
        session['user_role'] = user.user_role
        session['user_phone_num'] = user.user_phone_num
        session.permanent = True
        return jsonify({
            'message': 'Đăng nhập thành công',
            'role': user.user_role
        }), 200
    
    return jsonify({'error': 'Email hoặc mật khẩu không đúng'}), 401
    

@bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' in session:
        print("SESSION:", session)
        return jsonify({
            'user_id': session['user_id'],
            'user_name': session['user_name'],
            'user_email': session['user_email'],
            'user_phone_num': session.get('user_phone_num', ''),
            'user_avatar': session.get('user_avatar', ''),
            'user_role': session['user_role']
        }), 200
    return jsonify({'error': 'Chưa đăng nhập', 'user_role': 'guest'}), 401




@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Đăng xuất thành công'}), 200



google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@bp.route('/google/login')
def google_login():
    # redirect_uri = url_for('auth.google_callback', _external=True)
    redirect_uri = url_for('auth.google_callback', _external=True, _scheme='https')
    return google.authorize_redirect(redirect_uri)


@bp.route('/google/callback')
def google_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            user_info = google.parse_id_token(token)
    except OAuthError as e:
        print(f"Người dùng đã hủy đăng nhập hoặc có lỗi OAuth: {e}")
        return redirect('/login') 

    email = user_info['email']
    name = user_info.get('name', email)
    avatar = user_info.get('picture', '')

    # Tìm user
    user = User.query.filter_by(user_email=email).first()

    if not user:
        # Nếu chưa có thì tạo user mới
        user = User(
            user_email=email,
            user_password='',  # Vì đăng nhập Google, không cần mật khẩu
            user_name=name,
            user_avatar=avatar,
            user_status=True
        )
        # Gán role mặc định
        from backend.Models.rbac_model import Role
        default_role = Role.query.filter_by(role_name='user').first()
        if default_role:
            user.roles.append(default_role)

        db.session.add(user)
        db.session.commit()

    # Cập nhật session
    session['user_id'] = user.user_id
    session['user_name'] = user.user_name
    session['user_email'] = user.user_email
    session['user_avatar'] = user.user_avatar
    session['user_role'] = [role.role_name for role in user.roles]
    session['permissions'] = list(user.permissions)
    session.permanent = True

    return redirect('/')
