# controller/user_controller.py
from datetime import datetime, timedelta
from flask import request, jsonify, session, current_app
from backend.Models.users_model import User
from backend.extensions import db, bcrypt
from backend.utils.token_utils import verify_reset_token
import os
from zoneinfo import ZoneInfo 


# Cấu hình upload avatar
UPLOAD_FOLDER = 'frontend/static/image/user'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def edit_user_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.form

    new_name = data.get('user_name')
    new_phone = data.get('user_phone_num')
    new_email = data.get('user_email')

    if new_phone:
        if not new_phone.isdigit() or len(new_phone) != 10:
            return jsonify({'error': 'Số điện thoại phải gồm 10 chữ số'}), 400
        existing_phone = User.query.filter(
            User.user_phone_num == new_phone,
            User.user_id != user_id
        ).first()
        if existing_phone:
            return jsonify({'error': 'Số điện thoại đã được đăng ký'}), 400
        user.user_phone_num = new_phone

    if new_email:
        existing_email = User.query.filter(
            User.user_email == new_email,
            User.user_id != user_id
        ).first()
        if existing_email:
            return jsonify({'error': 'Email đã được đăng ký'}), 400
        user.user_email = new_email

    if new_name:
        user.user_name = new_name

    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{user_id}_avatar.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            if user.user_avatar:
                old_path = os.path.join('frontend', user.user_avatar.lstrip('/'))
                if os.path.exists(old_path) and os.path.basename(old_path) != filename:
                    os.remove(old_path)

            file.save(filepath)
            user.user_avatar = f"/static/image/user/{filename}"

    try:
        db.session.flush()
        db.session.commit()

        session['user_name'] = user.user_name
        session['user_phone_num'] = user.user_phone_num
        session['user_email'] = user.user_email
        session['user_avatar'] = user.user_avatar
        session.modified = True

        return jsonify({
            'message': 'Cập nhật thành công',
            'user_id': user.user_id,
            'user_name': user.user_name,
            'user_email': user.user_email,
            'user_phone_num': user.user_phone_num,
            'user_avatar': user.user_avatar,
            'role': user.user_role
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Lỗi khi cập nhật profile: {e}")
        return jsonify({'error': 'Lỗi hệ thống'}), 500




def recover_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({'success': False, 'message': 'Thiếu email'}), 400

    user = User.query.filter_by(user_email=email).first()
    
    if not user:
        return jsonify({'success': True, 'message': 'Nếu email tồn tại, bạn sẽ nhận được hướng dẫn'}), 200

    from backend.utils.token_utils import generate_reset_token
    token = generate_reset_token(email)
    reset_link = f"http://localhost:5000/reset-password/{token}"


    # --> LƯU token & hạn sử dụng
    expiry_seconds = current_app.config['RESET_TOKEN_EXPIRY_SECONDS']

    vn_now = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))
    user.user_reset_token      = token
    user.user_reset_expire_at  = vn_now + timedelta(seconds=expiry_seconds)
    db.session.commit()  

    from backend.Controllers.mail_controller import send_email
    subject = "🔐 Đặt lại mật khẩu tài khoản FireDetect"
    html_body = f"""
    <table style="width:100%; max-width:600px; margin:0 auto; font-family:Arial,sans-serif; background:#f9f9f9; padding:20px; border-radius:8px;">
        <tr>
            <td style="text-align:center;">
                <h2 style="color:#e63946;">🔐 Yêu cầu đặt lại mật khẩu</h2>
            </td>
        </tr>
        <tr>
            <td>
                <p>Xin chào <strong>{user.user_name}</strong>,</p>
                <p>Bạn (hoặc ai đó) đã yêu cầu đặt lại mật khẩu cho tài khoản<strong></strong>.</p>
                <p>Vui lòng nhấn vào nút bên dưới để tiếp tục. Liên kết sẽ hết hạn sau <strong>{int(expiry_seconds/60)} phút.</strong></p>
                <br />
                <div style="text-align:center; margin:20px 0;">
                    <a href="{reset_link}" style="background:#1d3557; color:#fff; padding:12px 24px; border-radius:4px; text-decoration:none; font-weight:bold;">
                        Đặt lại mật khẩu
                    </a>
                </div>
                <br />
                <p>Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này. Mật khẩu hiện tại của bạn sẽ không bị thay đổi.</p>
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


    send_email(subject, html_body, email)
    return jsonify({'success': True, 'message': 'Nếu email tồn tại, bạn sẽ nhận được hướng dẫn'}), 200


def submit_reset_password(token: str):
    """
    Xử lý URL /reset-password/<token> (AJAX POST):
        1. Xác thực token (itsdangerous)
        2. So khớp token + hạn từ DB
        3. Nhận mật khẩu mới, cập nhật và xoá token
    """
    # 1) Giải mã token (chữ ký + max_age)
    email = verify_reset_token(token)
    if not email:
        return jsonify(success=False,
                       message='Token không hợp lệ hoặc đã hết hạn'), 400

    # 2) Lấy user + kiểm tra token/hạn
    user = User.query.filter_by(user_email=email).first()
    if (not user or
        user.user_reset_token != token or
        user.user_reset_expire_at is None or
        user.user_reset_expire_at < datetime.utcnow()):
        return jsonify(success=False,
                       message='Token đã hết hạn hoặc không khớp'), 400

    # 3) Lấy mật khẩu mới
    data = request.get_json(silent=True) or {}
    new_password = data.get('new_password', '').strip()
    if len(new_password) < 6:
        return jsonify(success=False,
                       message='Mật khẩu phải có ít nhất 6 ký tự'), 400

    # 4) Cập nhật mật khẩu & xoá token
    user.user_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.user_reset_token = None
    user.user_reset_expire_at = None
    db.session.commit()

    return jsonify(success=True,
                   message='Đặt lại mật khẩu thành công'), 200
