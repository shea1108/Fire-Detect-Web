# backend/Routes/routes.py
from flask import Blueprint, render_template
import os
from flask import Blueprint, render_template, session, redirect, url_for
from backend.utils.auth_utils import login_required_redirect
from backend.Models.users_model import User

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
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return redirect(url_for('web.home'))
    return render_template('sign-up.html', user=user)




@bp.route('/profile')
@bp.route('/profile.html')
@login_required_redirect
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return render_template('sign-in.html')

    return render_template('profile.html', user=user)

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



