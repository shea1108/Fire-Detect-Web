# backend/Routes/routes.py
from flask import Blueprint, render_template, current_app
import os
from flask import Blueprint, render_template, session, redirect, url_for
from backend.utils.auth_utils import login_required_redirect
from backend.Models.users_model import User
from backend.Controllers.user_controller import render_verify_page

TEMPLATE_DIR= os.path.join(os.path.dirname(__file__), '../../frontend/templates')
bp = Blueprint('web', __name__, template_folder=TEMPLATE_DIR)

@bp.route('/')
@bp.route('/index.html')
@bp.route('/index')
def home():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('index.html', user=user)


@bp.route('/about')
@bp.route('/about.html')     
def about():
    return render_template('about.html')   


@bp.route('/register/verify-otp')
def show_verify_otp_page():
    return render_template('verify-otp.html')

#
@bp.route('/sign-in')
@bp.route('/sign-in.html')
def sign_in():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if 'admin' in session.get('user_role', []):
            return redirect('/admin/')
        else:
            return redirect('/')

    return render_template('sign-in.html', user=user)


@bp.route('/sign-up')
@bp.route('/sign-up.html')
def sign_up():
    if 'user_id' in session:
        return redirect(url_for('web.home')) 
    recaptcha_site_key = os.getenv('RECAPTCHA_SITE_KEY')
    return render_template('sign-up.html', recaptcha_site_key=recaptcha_site_key)




@bp.route('/profile')
@bp.route('/profile.html')
@login_required_redirect
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return render_template('sign-in.html')

    return render_template('profile.html', user=user)


@bp.route('/profile/verify-email-change')
@login_required_redirect
def render_profile_verify_page():
    return render_verify_page()

######################
@bp.route('/detect-image')
@bp.route('/detect-image.html')
def detect_image():
    return render_template('detect-image.html')

@bp.route('/detect-video')
@bp.route('/detect-video.html')
def detect_video():
    return render_template('detect-video.html')

@bp.route('/detect-camera')
@bp.route('/detect-camera.html')
def detect_camera():
    return render_template('detect-camera.html')

@bp.route('/logs')
@bp.route('/user_logs.html')
def user_logs():
    return render_template('user_logs.html')

##########
@bp.route('/recover-password', methods=['GET'])
@bp.route('/recover-password.html', methods=['GET'])
def show_recover_form():
    return render_template('recover-password.html')

@bp.route('/reset-password/<token>', methods=['GET'])
def show_reset_form(token):
    from backend.utils.token_utils import verify_reset_token
    email = verify_reset_token(token)
    if not email:
        return "Link không hợp lệ hoặc đã hết hạn", 400
    return render_template('reset-password.html', token=token)



@bp.route('/change-password', methods=['GET'])
def change_password():
    return render_template('change-password.html', recaptcha_site_key=current_app.config['RECAPTCHA_SITE_KEY'])


@bp.route('/otp-change-password', methods=['GET'])
def render_otp_change_password():
    return render_template('otp-change-password.html')
