# backend/Controllers/model_controller.py

from flask import jsonify
from backend.Models.models_model import Model
from backend.extensions import db

# Lấy tất cả mô hình
def get_all_models():
    try:
        models = Model.query.all()
        models_list = [
            {"model_id": m.model_id, "model_name": m.model_name}
            for m in models
        ]
        return jsonify({"models": models_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy model theo ID
def get_model_by_id(model_id):
    model = Model.query.get(model_id)
    if model:
        return jsonify({
            "model_id": model.model_id,
            "model_name": model.model_name
        })
    return jsonify({"error": "Model không tồn tại"}), 404

# Tạo model mới
def create_model(data):
    model_name = data.get("model_name")
    model_path = data.get("model_path")
    if not model_name or not model_path:
        return jsonify({"error": "Thiếu tên hoặc đường dẫn model"}), 400

    new_model = Model(model_name=model_name, model_path=model_path)
    db.session.add(new_model)
    db.session.commit()
    return jsonify({"message": "Tạo mô hình thành công", "model_id": new_model.model_id})

# Cập nhật model
def update_model(model_id, data):
    model = Model.query.get(model_id)
    if not model:
        return jsonify({"error": "Model không tồn tại"}), 404

    model.model_name = data.get("model_name", model.model_name)
    model.model_path = data.get("model_path", model.model_path)
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công"})

# Xóa model
def delete_model(model_id):
    model = Model.query.get(model_id)
    if not model:
        return jsonify({"error": "Model không tồn tại"}), 404

    db.session.delete(model)
    db.session.commit()
    return jsonify({"message": "Đã xóa mô hình"})
