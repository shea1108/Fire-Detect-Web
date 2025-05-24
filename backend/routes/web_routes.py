from flask import Blueprint, render_template, send_from_directory

web_bp = Blueprint("web", __name__)

@web_bp.route('/')
def homepage():
    return render_template('index.html')

@web_bp.route('/<path:path>')
def serve_static_file(path):
    return send_from_directory('frontend', path)
