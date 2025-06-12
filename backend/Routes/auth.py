##### backend/routes/auth.py
from flask import Blueprint, request, jsonify
from backend.Controllers.auth_controller import register_user, login_user
from flask import session
from backend.extensions import oauth
from flask import redirect, url_for
from authlib.integrations.base_client.errors import OAuthError
from backend.Models.users_model import User, db
import os
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
        print("SESSION:", session)
        return jsonify({
            'user_id': session['user_id'],
            'user_name': session['user_name'],
            'user_email': session['user_email'],
            'user_phone_num': session.get('user_phone_num', ''),
            'user_avatar': session.get('user_avatar', ''),
            'role': session['user_role']
        }), 200
    return jsonify({'error': 'Chưa đăng nhập'}), 401




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
    redirect_uri = url_for('auth.google_callback', _external=True)
    # redirect_uri = url_for('auth.google_callback', _external=True, _scheme='https')
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

    user = User.query.filter_by(user_email=email).first()
    avatar = user_info.get('picture', '')
    if not user:
        user = User(
            user_email=email,
            user_password='',
            user_name=name,
            user_role='user',
            user_avatar=avatar,
            user_status=True
        )
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.user_id
    session['user_name'] = user.user_name
    session['user_email'] = user.user_email
    session['user_role'] = user.user_role
    session['user_avatar'] = user.user_avatar 
    session.permanent = True

    return redirect('/')