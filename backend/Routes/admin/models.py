# backend/Routes/admin/models.py

from flask import Blueprint, jsonify
from backend.Models.models_model import Model
from backend.decorators.auth_decorators import admin_required

bp = Blueprint("admin_models", __name__, url_prefix="/api/admin/models")

@bp.route("/", methods=["GET"])
@admin_required
def get_all_models():
    models = Model.query.order_by(Model.model_create_at.desc()).all()
    data = [
        {
            "id": model.model_id,
            "name": model.model_name,
            "path": model.model_path,
            "status": model.model_status,
            "created_at": model.model_create_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for model in models
    ]
    return jsonify({"success": True, "data": data})
