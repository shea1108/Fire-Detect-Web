from backend.Controllers.notification_controller import create_notification, send_email_notification
from backend.Models.logs_model import Log
from backend.Models.devices_model import Device
from backend.Models.users_model import User
from backend.Models.notifications_model import Notification

SEND_NOTIFICATION_EMAIL = True

def handle_post_log_events(log_id: int, user_id: int, user_email: str, user_name: str):
    try:
        log = Log.query.get(log_id)
        if not log:
            print(f"Không tìm thấy log_id={log_id}")
            return False, "Log không tồn tại", None

        device = Device.query.get(log.dev_id)
        if not device or device.user_id != user_id:
            print(f"Thiết bị không hợp lệ hoặc không thuộc user. dev_id={log.dev_id}, user_id={user_id}")
            return False, "Thiết bị không thuộc user", None

        existing_noti = Notification.query\
            .join(Log, Notification.log_id == Log.log_id)\
            .filter(Log.dev_id == device.dev_id)\
            .first()
        if existing_noti:
            msg = f"Thiết bị {device.dev_name} ({device.dev_id}) đã có notification trước đó"
            print(msg + f" (noti_id={existing_noti.noti_id})")
            return True, msg, existing_noti.noti_id

        notification, err = create_notification(log_id)
        if not notification:
            print(f"Tạo notification thất bại: {err}")
            return False, f"Không tạo được notification: {err}", None
        print(f"Đã tạo notification mới (noti_id={notification.noti_id})")

        if SEND_NOTIFICATION_EMAIL and user_email:
            ok, msg = send_email_notification(notification.noti_id, user_email, user_name)
            print(f"[📧 EMAIL] {msg}")
            return ok, msg, notification.noti_id

        return True, "Notification được tạo nhưng không có email để gửi", notification.noti_id

    except Exception as e:
        import traceback
        print(f"Exception khi xử lý hậu log cho log_id={log_id}: {e}")
        traceback.print_exc()
        return False, f"Lỗi xử lý hậu log: {e}", None
