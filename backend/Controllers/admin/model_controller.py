# backend/Controllers/admin/model_controller.py
import os
from werkzeug.utils import secure_filename
from flask import request, jsonify
from backend.Models.models_model import Model
from backend.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo


def get_all_models():
    from backend.Models.models_model import Model

    models = Model.query.order_by(Model.model_id).all()
    data = [
        {
            "id": model.model_id,
            "name": model.model_name,
            "path": model.model_path,
            "short_title": model.model_short_title,
            "tooltip": model.model_tooltip,
            "status": model.model_status,
            "created_at": model.model_create_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for model in models
    ]
    return {"success": True, "data": data}



def create_model():
    form = request.form
    file = request.files.get("model_file")

    name = form.get("name", "").strip()
    raw_filename = form.get("path", "").strip()

    # Kiểm tra tên file hợp lệ
    if '/' in raw_filename or '\\' in raw_filename or not raw_filename.endswith(".pt"):
        return jsonify({"success": False, "message": "Tên file phải có định dạng <tên>.pt và không chứa dấu /"}), 400

    if not name:
        return jsonify({"success": False, "message": "Thiếu tên mô hình."}), 400

    # Đường dẫn lưu trong DB sẽ là Yolo/<tên>.pt
    model_path = f"Yolo/{raw_filename}"

    # Kiểm tra trùng tên trong DB
    if Model.query.filter_by(model_name=name).first():
        return jsonify({"success": False, "message": "Tên mô hình đã tồn tại."}), 400
    if Model.query.filter_by(model_path=model_path).first():
        return jsonify({"success": False, "message": "Đường dẫn đã tồn tại."}), 400

    # Kiểm tra file hợp lệ
    if not file or not file.filename.endswith(".pt"):
        return jsonify({"success": False, "message": "Vui lòng chọn file .pt"}), 400

    MAX_SIZE_MB = 200
    if file.content_length and file.content_length > MAX_SIZE_MB * 1024 * 1024:
        return jsonify({"success": False, "message": "Dung lượng file vượt quá 200MB"}), 400

    # ✅ Lưu file vào thư mục Yolo/
    try:
        save_dir = os.path.join("Yolo")
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.join(save_dir, raw_filename)
        if os.path.exists(save_path):
            return jsonify({"success": False, "message": "File .pt đã tồn tại trong thư mục YOLO."}), 400

        file.save(save_path)
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi lưu file: {str(e)}"}), 500

    # ✅ Lưu vào DB
    try:
        model = Model(
            model_name=name,
            model_path=model_path,
            model_short_title=form.get("short_title", "").strip(),
            model_tooltip=form.get("tooltip", "").strip(),
            model_status=form.get("status", "true").lower() == "true",
            model_create_at=datetime.utcnow(),
        )
        db.session.add(model)
        db.session.commit()
        return jsonify({"success": True, "message": "Thêm mô hình thành công."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400




def soft_delete_model(model_id):
    model = Model.query.get(model_id)
    if not model:
        return jsonify({"success": False, "message": "Model not found"}), 404
    try:
        model.model_status = False
        db.session.commit()
        return jsonify({"success": True, "message": "Model marked as inactive."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400



def get_one_model(model_id):
    model = Model.query.get(model_id)
    if not model:
        return jsonify({"success": False, "message": "Model not found"}), 404

    data = {
        "id": model.model_id,
        "name": model.model_name,
        "path": model.model_path,
        "short_title": model.model_short_title,
        "tooltip": model.model_tooltip,
        "status": model.model_status,
        "created_at": model.model_create_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return jsonify({"success": True, "data": data})






def update_model(model_id):
    model = Model.query.get(model_id)
    if not model:
        return jsonify({"success": False, "message": "Model not found."}), 404

    form = request.form
    file = request.files.get("model_file")

    name = form.get("name", "").strip()
    raw_filename = form.get("path", "").strip()
    short_title = form.get("short_title", "").strip()
    tooltip = form.get("tooltip", "").strip()
    status = form.get("status", "true").lower() == "true"

    # Kiểm tra hợp lệ
    if '/' in raw_filename or '\\' in raw_filename or not raw_filename.endswith(".pt"):
        return jsonify({"success": False, "message": "Tên file phải có định dạng <tên>.pt và không chứa dấu /"}), 400
    if not name:
        return jsonify({"success": False, "message": "Thiếu tên mô hình."}), 400

    new_model_path = f"Yolo/{raw_filename}"  # đường dẫn mới

    try:
        # ✅ Nếu có file mới thì lưu đè
        if file:
            if not file.filename.endswith(".pt"):
                return jsonify({"success": False, "message": "File phải có định dạng .pt"}), 400
            if file.content_length and file.content_length > 200 * 1024 * 1024:
                return jsonify({"success": False, "message": "Dung lượng file vượt quá 200MB"}), 400

            save_dir = os.path.join("Yolo")
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, raw_filename)

            # ✅ Nếu file cũ tồn tại thì xoá
            old_file_path = os.path.join("Yolo", os.path.basename(model.model_path))
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except Exception as e:
                    return jsonify({"success": False, "message": f"Lỗi khi xoá file cũ: {str(e)}"}), 500

            file.save(save_path)


        # ✅ Nếu đổi tên file .pt (nhưng không upload file mới) → rename file cũ
        elif model.model_path != new_model_path:
            old_path = os.path.join("Yolo", os.path.basename(model.model_path))
            new_path = os.path.join("Yolo", raw_filename)

            if os.path.exists(old_path):
                os.rename(old_path, new_path)
            else:
                return jsonify({"success": False, "message": f"Không tìm thấy file gốc {old_path} để đổi tên"}), 400

        # ✅ Cập nhật DB
        model.model_name = name
        model.model_path = new_model_path
        model.model_short_title = short_title
        model.model_tooltip = tooltip
        model.model_status = status

        db.session.commit()
        return jsonify({"success": True, "message": "Cập nhật mô hình thành công."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400
