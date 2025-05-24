from flask import Blueprint, send_from_directory
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# /admin => Giao diện admin chính
@admin_bp.route('/')
def admin_home():
    return send_from_directory(os.path.join('frontend', 'admin'), 'index.html')

# /admin/<path> => Các file tĩnh của admin như css, js, img...
@admin_bp.route('/<path:path>')
def admin_static(path):
    return send_from_directory(os.path.join('frontend', 'admin'), path)
