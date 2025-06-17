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
########### DASHBOARD ROUTES ###########
@bp.route('/')
@admin_required
def dashboard():
    return render_template('admin/index.html')




############ MODELS ROUTES STARTS ############
@bp.route("/models", methods=["GET"])
@admin_required
def models_list_page():
    return render_template("admin/admin_models.html")


@bp.route("/models/create", methods=["GET"])
@admin_required
def create_models_page():
    return render_template("admin/admin_models_create.html")


@bp.route("/models/edit/<int:model_id>", methods=["GET"])
@admin_required
def edit_model_page(model_id):
    return render_template("admin/admin_models_edit.html", model_id=model_id)
############ MODELS ROUTES ENDS ############





















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
