# backend/Controllers/auth_controller.py
import random
import string
import bcrypt
from datetime import datetime, timedelta
from flask import jsonify, session, current_app, redirect, url_for
from authlib.integrations.base_client.errors import OAuthError

from backend.Models.users_model import User
from backend.Models.rbac_model import Role
from backend.extensions import db, oauth, bcrypt
from backend.Controllers.mail_controller import send_email

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def register_send_otp(data):
    required_fields = ['user_name', 'user_email', 'user_password', 'user_role']
    if not all(data.get(f) for f in required_fields):
        return jsonify({"error": "Vui lòng điền đầy đủ các trường bắt buộc."}), 400

    if User.query.filter_by(user_email=data['user_email'], user_status=True).first():
        return jsonify({"error": "Email này đã được sử dụng."}), 409

    otp = generate_otp()
    hashed_password = bcrypt.generate_password_hash(data['user_password']).decode('utf-8')

    subject = "🔐 Mã Xác Thực Đăng Ký Tài Khoản"
    OTP_expiry_seconds = current_app.config['REGISTER_OTP_EXPIRY_SECONDS']

    html_body = f"""
        <table style="width:100%; max-width:600px; margin:0 auto; font-family:Arial,sans-serif; background:#f9f9f9; padding:20px; border-radius:8px;">
            <tr>
                <td style="text-align:center;">
                    <h2 style="color:#1d3557;">🔐 Xác Thực Đăng Ký Tài Khoản</h2>
                </td>
            </tr>
            <tr>
                <td>
                    <p>Xin chào <strong>{data['user_name']}</strong>,</p>
                    <p>Cảm ơn bạn đã đăng ký tài khoản tại <strong>FireDetect</strong>.</p>
                    <p>Mã xác thực (OTP) của bạn là:</p>
                    <div style="text-align:center; margin:20px 0;">
                        <span style="display:inline-block; background:#1d3557; color:#fff; padding:12px 24px; border-radius:6px; font-size:20px; letter-spacing:4px; font-weight:bold;">
                            {otp}
                        </span>
                    </div>
                    <p>Mã này sẽ hết hạn sau <strong>{int(OTP_expiry_seconds/60)} phút</strong>. Vui lòng không chia sẻ mã này với bất kỳ ai.</p>
                    <br />
                    <p>Nếu bạn không thực hiện hành động này, vui lòng bỏ qua email này.</p>
                    <br />
                    <p>Trân trọng,<br />Đội ngũ FireDetect</p>
                </td>
            </tr>
            <tr>
                <td style="text-align:center; font-size:12px; color:#888; padding-top:30px;">
                    &copy; {datetime.utcnow().year} FireDetect. All rights reserved.
                </td>
            </tr>
        </table>
        """

    success, _ = send_email(subject, html_body, data['user_email'])
    if not success:
        return jsonify({"error": "Không thể gửi email xác thực. Vui lòng thử lại."}), 500

    role = Role.query.filter_by(role_id=3).first()
    if not role:
        return jsonify({"error": "Vai trò mặc định không tồn tại."}), 500

    session['registration_data'] = {
        'user_name': data['user_name'],
        'user_email': data['user_email'],
        'user_password': hashed_password,
        'user_phone_num': data.get('user_phone_num'),
        'user_role': role.role_name,
        'user_status': True,
        'otp': otp,
        'expiry': (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    }
    session.permanent = True
    return jsonify({
        "message": "Mã OTP đã được gửi đến email của bạn.",
        "email": data['user_email']
    }), 200


def register_verify_otp(data):
    reg = session.get('registration_data')
    if not reg or reg.get('user_email') != data.get('email'):
        return jsonify({"error": "Phiên đăng ký không hợp lệ hoặc đã hết hạn."}), 400
    if reg['otp'] != data.get('otp'):
        return jsonify({"error": "Mã OTP không chính xác."}), 400
    if datetime.utcnow() > datetime.fromisoformat(reg['expiry']):
        session.pop('registration_data', None)
        return jsonify({"error": "Mã OTP đã hết hạn."}), 400

    new_user = User(
        user_name=reg['user_name'],
        user_email=reg['user_email'],
        user_password=reg['user_password'],
        user_phone_num=reg.get('user_phone_num'),
        user_status=True
    )
    role = Role.query.filter_by(role_id=3).first()
    if not role:
        return jsonify({"error": "Vai trò không hợp lệ"}), 400
    new_user.roles.append(role)

    try:
        db.session.add(new_user)
        db.session.commit()
        session.pop('registration_data', None)
        return jsonify({"message": "Đăng ký tài khoản thành công!"}), 201
    except Exception as e:
        db.session.rollback()
        print("Lỗi DB:", e)
        return jsonify({"error": "Lỗi khi tạo tài khoản"}), 500

def login_user(data):
    email = data.get('user_email')
    password = data.get('user_password')

    user = User.query.filter_by(user_email=email, user_status=True).first()
    if not user:
        return jsonify({'error': 'Email hoặc mật khẩu không đúng'}), 401

    if not user.user_password or not bcrypt.check_password_hash(user.user_password, password):
        return jsonify({'error': 'Sai email hoặc mật khẩu'}), 401

    session['user_id'] = user.user_id
    session['user_name'] = user.user_name
    session['user_email'] = user.user_email
    session['user_avatar'] = user.user_avatar
    session['user_phone_num'] = user.user_phone_num
    session['user_role'] = [r.role_name for r in user.roles]
    session['permissions'] = list(user.permissions)
    session.permanent = True

    return jsonify({
        'message': 'Đăng nhập thành công',
        'user_id': user.user_id,
        'user_role': session['user_role'],
        'permissions': session['permissions']
    }), 200

def handle_google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo') or oauth.google.parse_id_token(token)
    except OAuthError as e:
        print("OAuth Error:", e)
        return redirect('/login')

    user = User.query.filter_by(user_email=user_info['email']).first()
    if not user:
        user = User(
            user_email=user_info['email'],
            user_name=user_info.get('name', ''),
            user_avatar=user_info.get('picture', ''),
            user_password='',
            user_status=True
        )
        default_role = Role.query.filter_by(role_id=3).first()
        if default_role:
            user.roles.append(default_role)
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.user_id
    session['user_name'] = user.user_name
    session['user_email'] = user.user_email
    session['user_avatar'] = user.user_avatar
    session['user_role'] = [r.role_name for r in user.roles]
    session['permissions'] = list(user.permissions)
    session.permanent = True

    return redirect('/')


def handle_google_login(user_info):
    email = user_info.get('email')
    name = user_info.get('name')
    avatar = user_info.get('picture')

    if not email:
        return jsonify({'error': 'Email không được cung cấp bởi Google'}), 400

    # Kiểm tra người dùng đã tồn tại chưa
    user = User.query.filter_by(user_email=email).first()

    if not user:
        # Mặc định role là user
        user_role = Role.query.filter_by(role_name='user').first()
        if not user_role:
            return jsonify({'error': 'Vai trò mặc định không tồn tại'}), 500

        # Tạo mật khẩu random và hash bằng bcrypt
        random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        hashed_password = bcrypt.generate_password_hash(random_password).decode('utf-8')

        user = User(
            user_name=name,
            user_email=email,
            user_password=hashed_password,
            user_avatar=avatar
        )
        user.roles.append(user_role)
        db.session.add(user)
        db.session.commit()

    # Lưu thông tin vào session
    user_roles = [role.role_name for role in user.roles]
    session['user_id'] = user.user_id
    session['user_name'] = user.user_name
    session['user_email'] = user.user_email
    session['user_avatar'] = user.user_avatar or ''
    session['user_phone_num'] = user.user_phone_num or ''
    session['user_role'] = user_roles
    session['permissions'] = [perm.permission_name for role in user.roles for perm in role.permissions]

    # Điều hướng: nếu có admin → /admin/, còn lại →
    if 'admin' in user_roles:
        return redirect('/admin/')
    return redirect('/')