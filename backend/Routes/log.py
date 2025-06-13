# backend/Routes/log.py
from flask import Blueprint, request, jsonify
from backend.Controllers.log_controller import handle_detect_from_api

bp = Blueprint("log", __name__, url_prefix="/api/log")

@bp.route("/", methods=["POST"])
def post_detect_log():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Thiếu dữ liệu JSON"}), 400

        result = handle_detect_from_api(data)

        return jsonify({
            "success": result["success"],
            "message": result["message"],
            "detections": result.get("detections", []),
            "log_id": result.get("log_id")
        }), 200 if result["success"] else 400

    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {e}"}), 500
