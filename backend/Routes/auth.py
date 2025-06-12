# backend/Routes/auth.py
import os
from flask import Blueprint, request, jsonify, session, redirect, url_for
from backend.Controllers import auth_controller
from backend.extensions import oauth
from authlib.integrations.base_client.errors import OAuthError

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Gửi OTP
@bp.route('/register/send-otp', methods=['POST'])
def send_otp():
    return auth_controller.register_send_otp(request.json)

# Xác minh OTP và tạo tài khoản
@bp.route('/register/verify-otp', methods=['POST'])
def verify_otp():
    reg = session.get('registration_data')
    if not reg:
        return jsonify({'error': 'Không hợp lệ hoặc đã hết hạn'}), 403
    return auth_controller.register_verify_otp(request.json)

# Đăng nhập
@bp.route('/login', methods=['POST'])
def login():
    return auth_controller.login_user(request.json)

# Thông tin người dùng hiện tại (dành cho FE)
@bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' in session:
        return jsonify({
            'user_id': session['user_id'],
            'user_name': session['user_name'],
            'user_email': session['user_email'],
            'user_phone_num': session.get('user_phone_num', ''),
            'user_avatar': session.get('user_avatar', ''),
            'user_role': session.get('user_role', []),
            'permissions': session.get('permissions', [])
        }), 200
    return jsonify({'error': 'Chưa đăng nhập', 'user_role': 'guest'}), 401

# Đăng xuất
@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Đăng xuất thành công'}), 200

# OAuth Google
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Bắt đầu Google Login
@bp.route('/google/login')
def google_login():
    #CHẠY SSL
    # redirect_uri = url_for('auth.google_callback', _external=True, _scheme='https')
    #CHẠY LOCALHOST
    redirect_uri = url_for('auth.google_callback', _external=True)

    return google.authorize_redirect(redirect_uri)

# Xử lý callback từ Google
@bp.route('/google/callback')
def google_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo') or google.parse_id_token(token)
        return auth_controller.handle_google_login(user_info)
    except OAuthError as e:
        print("OAuth Error:", e)
        return redirect('/login')
