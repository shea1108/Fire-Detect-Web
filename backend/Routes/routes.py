from flask import Blueprint, render_template
import os
bp = Blueprint('web', __name__)

@bp.route('/')
def home():
    return render_template('index-new.html')

@bp.route('/camera')
def camera():
    return render_template('detectcamera.html')

@bp.route('/picture')
def picture():
    return render_template('detectpicture.html')

@bp.route('/video')
def video():
    return render_template('detectvideo.html')

@bp.route('/login')
def login_page():
    return render_template('login.html')

@bp.route('/register')
def register_page():
    return render_template('register.html')




# Tự động tạo route cho tất cả template trong admin/
TEMPLATE_FOLDER_FE_NEW = os.path.join(os.path.dirname(__file__), '../../frontend/templates')
@bp.route('/<path:page>')
def render_new_frontend_page(page):
    if not page.endswith('.html'):
        page += '.html'

    full_path = os.path.join(TEMPLATE_FOLDER_FE_NEW, page)
    if os.path.exists(full_path):
        return render_template(page)  # Không có dấu /
    return f"404 - {page} not found", 404

