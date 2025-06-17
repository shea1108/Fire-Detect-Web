# backend/Routes/admin/models.py

from flask import Blueprint
from backend.Controllers.admin import model_controller
from backend.decorators.auth_decorators import admin_required

bp = Blueprint("admin_models", __name__, url_prefix="/api/admin/models")

@bp.route("/get-one/<int:model_id>", methods=["GET"])
@admin_required
def get_one_model(model_id):
    return model_controller.get_one_model(model_id)


@bp.route("/get-all", methods=["GET"])
@admin_required
def get_all_models():
    return model_controller.get_all_models()

@bp.route("/create", methods=["POST"])
@admin_required
def create_model():
    return model_controller.create_model()

@bp.route("/update/<int:model_id>", methods=["POST"])
@admin_required
def update_model(model_id):
    return model_controller.update_model(model_id)

@bp.route("/soft-delete/<int:model_id>", methods=["PUT"])
@admin_required  # nếu có
def route_soft_delete_model(model_id):
    return model_controller.soft_delete_model(model_id)


