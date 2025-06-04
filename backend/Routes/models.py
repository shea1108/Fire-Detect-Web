from flask import Blueprint, request, jsonify
from backend.Controllers.model_controller import (
    get_all_models, get_model_by_id,
    create_model, update_model, delete_model
)

bp = Blueprint('models', __name__, url_prefix='/api/models')

@bp.route('/', methods=['GET'])
def get_models():
    try:
        return get_all_models()
    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"error": "Lỗi máy chủ"}), 500

@bp.route('/<int:model_id>', methods=['GET'])
def get_model(model_id):
    try:
        return get_model_by_id(model_id)
    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"error": "Lỗi máy chủ"}), 500

@bp.route('/', methods=['POST'])
def create():
    try:
        return create_model(request.json)
    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"error": "Lỗi máy chủ"}), 500

@bp.route('/<int:model_id>', methods=['PUT'])
def update(model_id):
    try:
        return update_model(model_id, request.json)
    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"error": "Lỗi máy chủ"}), 500

@bp.route('/<int:model_id>', methods=['DELETE'])
def delete(model_id):
    try:
        return delete_model(model_id)
    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"error": "Lỗi máy chủ"}), 500
