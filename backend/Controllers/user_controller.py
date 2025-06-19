# controller/user_controller.py
from datetime import datetime, timedelta
# <<< THÊM MỚI: Các import cần thiết từ Flask và thư viện chuẩn >>>
from flask import request, jsonify, session, current_app, render_template, redirect, url_for, flash
from backend.Models.users_model import User
from backend.extensions import db, bcrypt
from backend.utils.token_utils import verify_reset_token
import os
from zoneinfo import ZoneInfo 
import random # Thêm thư viện random để tạo OTP
from backend.Controllers.mail_controller import send_email # Giả định bạn có hàm này
import requests

# --- CẤU HÌNH VÀ HÀM HỖ TRỢ (GIỮ NGUYÊN) ---
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
    new_email = data.get('user_email').strip() if data.get('user_email') else None

    # <<< THAY ĐỔI: Tích hợp luồng gửi OTP khi đổi email >>>
    if new_email and new_email.lower() != user.user_email.lower():
        existing_email = User.query.filter(User.user_email == new_email, User.user_id != user_id).first()
        if existing_email:
            return jsonify({'error': 'Email đã được đăng ký'}), 400

        try:
            otp = str(random.randint(100000, 999999))
            session['email_change_otp'] = otp
            session['new_email_pending'] = new_email
            session['otp_expiry'] = (datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')) + timedelta(minutes=5)).isoformat()

            subject = "🔐 Xác thực thay đổi Email tài khoản FireDetect"
            html_body = f"""
            <table style="width:100%; max-width:600px; margin:0 auto; font-family:Arial,sans-serif; background:#f9f9f9; padding:20px; border-radius:8px;">
                <tr><td style="text-align:center;"><h2 style="color:#e63946;">🔐 Xác thực thay đổi Email</h2></td></tr>
                <tr><td>
                    <p>Xin chào <strong>{user.user_name}</strong>,</p>
                    <p>Bạn (hoặc ai đó) đã yêu cầu thay đổi địa chỉ email cho tài khoản của bạn.</p>
                    <p>Vui lòng nhập mã OTP bên dưới để xác thực địa chỉ email mới:</p>

                    <div style="text-align:center; margin:24px 0;">
                        <div style="display:inline-block; background:#1d3557; color:#fff; font-size:24px; font-weight:bold; padding:12px 24px; border-radius:6px;">
                            {otp}
                        </div>
                    </div>

                    <p>Mã này có hiệu lực trong <strong>5 phút</strong>. Nếu bạn không yêu cầu thay đổi email, vui lòng bỏ qua email này.</p>

                    <br /><p>Trân trọng,<br />Đội ngũ FireDetect</p>
                </td></tr>
                <tr><td style="text-align:center; font-size:12px; color:#888; padding-top:30px;">
                    &copy; {datetime.utcnow().year} FireDetect. All rights reserved.
                </td></tr>
            </table>
            """
            send_email(subject, html_body, new_email)

            # Trả về URL của trang xác thực để JavaScript chuyển hướng
            return jsonify({'redirect': url_for('web.render_profile_verify_page')}), 200

        except Exception as e:
            print(f"[ERROR] Lỗi khi gửi OTP đổi email: {e}")
            return jsonify({'error': 'Không thể gửi email xác thực. Vui lòng thử lại.'}), 500

    # --- Cập nhật các thông tin khác (nếu không đổi email) ---
    if new_phone:
        if not new_phone.isdigit() or len(new_phone) != 10:
            return jsonify({'error': 'Số điện thoại phải gồm 10 chữ số'}), 400
        existing_phone = User.query.filter(User.user_phone_num == new_phone, User.user_id != user_id).first()
        if existing_phone:
            return jsonify({'error': 'Số điện thoại đã được đăng ký'}), 400
        user.user_phone_num = new_phone

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
        db.session.commit()
        session['user_name'] = user.user_name
        session['user_phone_num'] = user.user_phone_num
        session['user_email'] = user.user_email
        session['user_avatar'] = user.user_avatar
        session.modified = True
        return jsonify({'message': 'Cập nhật thành công'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Lỗi khi cập nhật profile: {e}")
        return jsonify({'error': 'Lỗi hệ thống'}), 500

# <<< HÀM MỚI: Dùng để hiển thị trang nhập OTP khi đổi email >>>
def render_verify_page():
    if 'user_id' not in session or 'new_email_pending' not in session:
        flash('Phiên làm việc không hợp lệ. Vui lòng thử lại từ trang thông tin tài khoản.', 'warning')
        return redirect(url_for('web.profile')) 

    new_email = session.get('new_email_pending')
    return render_template('profile_verify_otp.html', new_email=new_email)

# <<< HÀM MỚI: Dùng để xử lý form submit OTP khi đổi email >>>
def verify_email_change():
    if 'user_id' not in session:
        return redirect(url_for('web.sign_in'))

    submitted_otp = request.form.get('otp')
    stored_otp = session.get('email_change_otp')
    new_email = session.get('new_email_pending')
    otp_expiry_str = session.get('otp_expiry')

    if not all([submitted_otp, stored_otp, new_email, otp_expiry_str]):
        flash('Phiên làm việc không hợp lệ hoặc đã hết hạn.', 'danger')
        return redirect(url_for('web.render_profile_verify_page'))

    otp_expiry = datetime.fromisoformat(otp_expiry_str)
    if datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')) > otp_expiry:
        flash('Mã OTP đã hết hạn. Vui lòng thực hiện lại việc đổi email.', 'danger')
        session.pop('email_change_otp', None)
        session.pop('new_email_pending', None)
        session.pop('otp_expiry', None)
        session.modified = True
        return redirect(url_for('web.profile'))

    if submitted_otp != stored_otp:
        flash('Mã OTP không chính xác.', 'danger')
        return redirect(url_for('web.render_profile_verify_page'))

    user = User.query.get(session['user_id'])
    user.user_email = new_email

    try:
        db.session.commit()
        session['user_email'] = new_email
        session.pop('email_change_otp', None)
        session.pop('new_email_pending', None)
        session.pop('otp_expiry', None)
        session.modified = True
        flash('Cập nhật email thành công!', 'success')
        return redirect(url_for('web.profile'))
    except Exception as e:
        db.session.rollback()
        flash('Lỗi hệ thống khi cập nhật email.', 'danger')
        return redirect(url_for('web.render_profile_verify_page'))

# <<< CÁC HÀM KHÔI PHỤC MẬT KHẨU (GIỮ NGUYÊN) >>>
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
    expire_at = vn_now + timedelta(seconds=expiry_seconds)
    expire_str = expire_at.strftime('%H:%M:%S %d/%m/%Y')  # ví dụ: 12:05:30 17/06/2025
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
                    <p>Vui lòng nhấn vào nút bên dưới để tiếp tục.</p>
                    <p>Liên kết sẽ hết hạn sau <strong>{int(expiry_seconds / 60)} phút</strong>, tức vào lúc <strong>{expire_str}</strong> (giờ Việt Nam).</p>
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





def request_password_change():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Chưa đăng nhập'}), 401
    data = request.get_json()  # ✅ Cần có dòng này TRƯỚC khi dùng data.get
    recaptcha_token = data.get('g-recaptcha-response')
    if not recaptcha_token:
        return jsonify({'success': False, 'message': 'Thiếu mã reCAPTCHA'}), 400

    # Gửi request xác minh với Google
    recaptcha_secret = current_app.config.get("RECAPTCHA_SECRET_KEY")
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    payload = {
        'secret': recaptcha_secret,
        'response': recaptcha_token
    }
    try:
        r = requests.post(verify_url, data=payload)
        result = r.json()
        if not result.get('success'):
            return jsonify({'success': False, 'message': 'Xác minh reCAPTCHA thất bại'}), 400
    except Exception as e:
        print(f"[ERROR] Gửi xác minh reCAPTCHA: {e}")
        return jsonify({'success': False, 'message': 'Không thể xác minh reCAPTCHA'}), 500
    old_pw = data.get('old_password')
    new_pw = data.get('new_password')

    if not old_pw or not new_pw or len(new_pw.strip()) < 6:
        return jsonify({'success': False, 'message': 'Dữ liệu không hợp lệ'}), 400

    user = User.query.get(session['user_id'])
    if not user or not bcrypt.check_password_hash(user.user_password, old_pw):
        return jsonify({'success': False, 'message': 'Mật khẩu cũ không đúng'}), 400
    # 👉 Kiểm tra nếu mật khẩu mới trùng với mật khẩu cũ
    if bcrypt.check_password_hash(user.user_password, new_pw):
        return jsonify({'success': False, 'message': 'Mật khẩu mới không được trùng với mật khẩu cũ'}), 400
    # Lưu mật khẩu mới vào session
    session['pending_new_password'] = new_pw.strip()
    otp = str(random.randint(100000, 999999))
    session['change_pw_otp'] = otp
    session['change_pw_expiry'] = (datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) + timedelta(minutes=5)).isoformat()
    session.modified = True
    vn_now = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))
    expire_at = vn_now + timedelta(minutes=5)
    expire_str = expire_at.strftime('%H:%M:%S %d/%m/%Y')  # Ví dụ: 14:23:00 19/06/2025

    try:
        subject = "🔐 Xác Nhận Đổi Mật Khẩu Mới - FireDetect"
        html_body = f"""
            <table style="width:100%; max-width:600px; margin:0 auto; font-family:Arial,sans-serif; background:#f9f9f9; padding:20px; border-radius:8px;">
            <tr>
                <td style="text-align:center;">
                    <h2 style="color:#e63946;">🔐 Xác Nhận Đổi Mật Khẩu Mới</h2>
                </td>
            </tr>
            <tr>
                <td>
                    <p>Xin chào <strong>{user.user_name}</strong>,</p>
                    <p>Bạn (hoặc ai đó) đã yêu cầu đổi mật khẩu cho tài khoản của bạn.</p>
                    <p>Vui lòng nhập mã OTP bên dưới để xác thực việc đổi mật khẩu:</p>

                    <div style="text-align:center; margin:24px 0;">
                        <div style="display:inline-block; background:#1d3557; color:#fff; font-size:24px; font-weight:bold; padding:12px 24px; border-radius:6px;">
                            {otp}
                        </div>
                    </div>

                    <p>Mã này có hiệu lực trong <strong>5 phút</strong>, tức là đến <strong>{expire_str}</strong> (giờ Việt Nam).</p>
                    <p>Nếu bạn không yêu cầu đổi mật khẩu, vui lòng bỏ qua email này.</p>

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

        send_email(subject, html_body, user.user_email)
        return jsonify({'success': True, 'redirect': url_for('web.render_otp_change_password')}), 200
    except Exception as e:
        print(f"[ERROR] Gửi email OTP đổi mật khẩu: {e}")
        return jsonify({'success': False, 'message': 'Không thể gửi email xác thực'}), 500




def confirm_password_change():
    if 'user_id' not in session:
        return redirect(url_for('web.sign_in'))

    otp = request.form.get('otp')
    stored_otp = session.get('change_pw_otp')
    expiry_str = session.get('change_pw_expiry')
    new_pw = session.get('pending_new_password')

    if not all([otp, stored_otp, expiry_str, new_pw]):
        flash('Thông tin không hợp lệ hoặc đã hết hạn', 'danger')
        return redirect(url_for('web.render_otp_change_password'))

    if datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) > datetime.fromisoformat(expiry_str):
        flash('OTP đã hết hạn', 'danger')
        return redirect(url_for('web.render_otp_change_password'))

    if otp != stored_otp:
        flash('OTP không chính xác', 'danger')
        return redirect(url_for('web.render_otp_change_password'))

    user = User.query.get(session['user_id'])
    user.user_password = bcrypt.generate_password_hash(new_pw).decode('utf-8')

    try:
        db.session.commit()
        session.pop('pending_new_password', None)
        session.pop('change_pw_otp', None)
        session.pop('change_pw_expiry', None)
        session.modified = True
        flash('✅ Đổi mật khẩu thành công. Vui lòng đăng nhập lại.', 'success')
        return redirect(url_for('web.render_otp_change_password'))
    except Exception as e:
        db.session.rollback()
        flash('Lỗi hệ thống khi đổi mật khẩu', 'danger')
        return redirect(url_for('web.render_otp_change_password'))
