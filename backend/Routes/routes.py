from flask import Blueprint, render_template

bp = Blueprint('web', __name__)

@bp.route('/')
def home():
    return render_template('index.html')

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