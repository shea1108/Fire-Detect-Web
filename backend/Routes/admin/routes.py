from flask import Blueprint, render_template, session
import os
from backend.decorators.auth_decorators import admin_required

bp = Blueprint('admin_routes', __name__, url_prefix='/admin')

TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), '../../../frontend/templates/admin')

# Inject trực tiếp từ session
@bp.context_processor
def inject_user_from_session():
    return dict(
        user_name=session.get("user_name"),
        user_avatar=session.get("user_avatar") or "/static/admin/assets/images/users/user.jpg"
    )

@bp.route('/')
@admin_required
def dashboard():
    return render_template('admin/index.html')

@bp.route('/<path:page>')
@admin_required
def render_admin_page(page):
    if not page.endswith('.html'):
        page += '.html'

    filename = f"admin/{page}"
    full_path = os.path.join(TEMPLATE_FOLDER, page)
    if os.path.exists(full_path):
        return render_template(filename)
    return f"404 - {filename} not found", 404
