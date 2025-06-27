# backend/Routes/log.py
from flask import Blueprint, request, jsonify, Response
from backend.Controllers.log_controller import handle_detect_from_api
from backend.Controllers.log_controller import (
    handle_detect_from_api, 
    get_all_logs_for_datatable, 
    get_log_details,
    export_logs_to_csv
)

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


# API để DataTables lấy dữ liệu
@bp.route("/get-all", methods=['POST'])
# @login_required
def api_get_all_logs():
    """
    API endpoint cho DataTables lấy dữ liệu log.
    Gọi controller để xử lý logic.
    """
    return get_all_logs_for_datatable()


# API để lấy chi tiết một log
@bp.route("/get-one/<int:log_id>", methods=['GET'])
# @login_required
def api_get_one_log(log_id):
    """
    API endpoint để lấy chi tiết một log khi người dùng click vào nút "Xem".
    """
    return get_log_details(log_id)



@bp.route("/export-csv", methods=['GET'])
def export_logs_csv():
    """
    API endpoint để xuất toàn bộ log dưới dạng CSV.
    """
    try:
        csv_data = export_logs_to_csv()
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=logs.csv"},
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

