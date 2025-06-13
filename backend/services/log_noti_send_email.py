from flask import session
from backend.Controllers.notification_controller import create_notification, send_email_notification
from backend.Models.logs_model import Log
from backend.Models.devices_model import Device
from backend.Models.users_model import User
from backend.Models.notifications_model import Notification

# ✅ Bật / tắt gửi email thông báo (debug dễ hơn)
SEND_NOTIFICATION_EMAIL = True

def handle_post_log_events(log_id: int):
    try:
        user_id = session.get("user_id")
        if not user_id:
            print("❌ Không có session user_id")
            return False, "❌ Phiên đăng nhập không hợp lệ. Bỏ qua notification", None

        log = Log.query.get(log_id)
        if not log:
            print(f"❌ Không tìm thấy log_id={log_id}")
            return False, "❌ Log không tồn tại", None

        device = Device.query.get(log.dev_id)
        if not device or device.user_id != user_id:
            print(f"❌ Thiết bị không hợp lệ hoặc không thuộc user. dev_id={log.dev_id}")
            return False, "❌ Thiết bị không thuộc user", None

        # ✅ Kiểm tra nếu đã có notification cho thiết bị
        existing_noti = Notification.query\
            .join(Log, Notification.log_id == Log.log_id)\
            .filter(Log.dev_id == device.dev_id)\
            .first()
        if existing_noti:
            print(f"✅ Thiết bị {device.dev_name} đã có notification trước đó (noti_id={existing_noti.noti_id})")
            return True, "✅ Thiết bị này đã có notification trước đó", existing_noti.noti_id

        user = User.query.get(user_id)
        recipient_email = user.user_email if user else None
        user_name = user.user_name if user else "Người dùng"

        # ✅ Tạo notification mới
        notification, err = create_notification(log_id)
        if not notification:
            print(f"❌ Tạo notification thất bại: {err}")
            return False, f"❌ Không tạo được notification: {err}", None
        print(f"✅ Đã tạo notification mới (noti_id={notification.noti_id})")

        # ✅ Gửi email nếu bật flag và có email
        if SEND_NOTIFICATION_EMAIL and recipient_email:
            ok, msg = send_email_notification(notification.noti_id, recipient_email, user_name)
            print(f"[📧 EMAIL] {msg}")
            return ok, msg, notification.noti_id

        return True, "✅ Notification được tạo nhưng không có email để gửi", notification.noti_id

    except Exception as e:
        print(f"❌ Exception khi xử lý hậu log: {e}")
        return False, f"❌ Lỗi xử lý hậu log: {e}", None
