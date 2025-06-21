# backend/services/log_noti_send_email.py
import logging
from flask import session, current_app
from backend.Controllers.notification_controller import create_notification, send_email_notification
from backend.Models.logs_model import Log
from backend.Models.devices_model import Device
from backend.Models.users_model import User
from backend.Models.notifications_model import Notification
from datetime import datetime, timedelta


def handle_post_log_events(log_id, user_email=None, user_name=None, origin_path=None, bbox_path=None):
    try:
        # Fallback: nếu không truyền user_email thì lấy từ session
        if not user_email or not user_name:
            user_id = session.get("user_id")
            if not user_id:
                logging.warning("❌ Không có session user_id và không truyền thủ công user info")
                return False, "❌ Không đủ thông tin người dùng", None
            user = User.query.get(user_id)
            if not user:
                logging.warning("❌ Không tìm thấy user từ session")
                return False, "❌ Không tìm thấy user", None
            user_email = user.user_email
            user_name = user.user_name
        else:
            user = User.query.filter_by(user_email=user_email).first()
            user_id = user.user_id if user else None

        log = Log.query.get(log_id)
        if not log:
            logging.warning(f"❌ Không tìm thấy log_id={log_id}")
            return False, "❌ Log không tồn tại", None

        device = Device.query.get(log.dev_id)
        if not device or (user_id and device.user_id != user_id):
            logging.warning(f"❌ Thiết bị không hợp lệ hoặc không thuộc user. dev_id={log.dev_id}")
            return False, "❌ Thiết bị không thuộc user", None

        # Kiểm tra cooldown 10 phút
        cooldown_minutes = 10
        threshold_time = datetime.now() - timedelta(minutes=cooldown_minutes)
        recent_noti = Notification.query.join(Log).filter(
            Log.dev_id == device.dev_id,
            Notification.noti_create_at >= threshold_time
        ).first()

        if recent_noti:
            logging.info(f"⏳ Thiết bị {device.dev_name} đã gửi thông báo trong {cooldown_minutes} phút gần đây (noti_id={recent_noti.noti_id})")
            return True, f"⏳ Đã gửi gần đây, bỏ qua", recent_noti.noti_id

        # Tạo notification mới
        notification, err = create_notification(log_id)
        if not notification:
            logging.error(f"❌ Tạo notification thất bại: {err}")
            return False, f"❌ Không tạo được notification: {err}", None

        logging.info(f"✅ Đã tạo notification mới (noti_id={notification.noti_id})")

        # === SỬA LỖI Ở ĐÂY ===
        # Lấy giá trị cấu hình từ app config
        # Giả sử bạn có biến này trong file config.py hoặc .env
        should_send_email = current_app.config.get("SEND_NOTIFICATION_EMAIL", True) 

        if should_send_email and user_email:
            # Truyền đầy đủ origin_path và bbox_path vào hàm gửi mail
            ok, msg = send_email_notification(
                notification.noti_id,
                user_email,
                user_name,
                origin_path=origin_path,
                bbox_path=bbox_path
            )
            logging.info(f"[📧 EMAIL] {msg}")
            return ok, msg, notification.noti_id

        return True, "✅ Notification được tạo nhưng không có email để gửi (do cấu hình)", notification.noti_id

    except Exception as e:
        logging.exception(f"❌ Exception khi xử lý hậu log: {e}")
        return False, f"❌ Lỗi xử lý hậu log: {str(e)}", None