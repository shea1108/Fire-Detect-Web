##### backend/Routes/admin/routes.py
from flask import Blueprint, render_template
import os
from backend.decorators.auth_decorators import admin_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Tự động tạo route cho tất cả template trong admin/
TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), '../../../frontend/templates/admin')



@bp.route('/')
@admin_required
def dashboard():
    return render_template('admin/index.html')

@bp.route('/<path:page>')
@admin_required
def render_admin_page(page):
    # Nếu người dùng đã truyền đầy đủ .html thì giữ nguyên, nếu chưa thì thêm vào
    if not page.endswith('.html'):
        page += '.html'

    filename = f"admin/{page}"
    full_path = os.path.join(TEMPLATE_FOLDER, page)
    if os.path.exists(full_path):
        return render_template(filename)
    return f"404 - {filename} not found", 404

