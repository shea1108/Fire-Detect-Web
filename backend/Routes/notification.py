from flask import Blueprint, request, jsonify
from backend.Controllers.notification_controller import send_email_notification
from flask import current_app



bp = Blueprint('notification', __name__, url_prefix='/api/notifications')

@bp.route('/send-email', methods=['POST'])
def api_send_email():
    try:
        data = request.get_json()
        noti_id = data.get("noti_id")
        email = data.get("email")

        if not noti_id or not email:
            return jsonify({"success": False, "message": "Thiếu `noti_id` hoặc `email`"}), 400

        ok, msg = send_email_notification(noti_id, email)
        return jsonify({"success": ok, "message": msg}), 200 if ok else 500

    except Exception as e:
        print("Lỗi gửi email:", e)
        return jsonify({"success": False, "message": "Lỗi server khi gửi email."}), 500
