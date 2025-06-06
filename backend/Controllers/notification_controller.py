from flask import current_app
from flask_mail import Message
from backend.extensions import mail, db
from backend.Models.notifications_model import Notification
from backend.Models.notification_models_model import NotificationPlatform
from datetime import datetime

def send_email_notification(noti_id: int, recipient_email: str):
    if not current_app.config.get("MAIL_ENABLED", False):
        print("🚫 Gửi email đã bị vô hiệu hóa (MAIL_ENABLED=False).")
        return True, "Gửi email đã bị tắt trong môi trường này."

    notification = Notification.query.get(noti_id)
    if not notification:
        return False, "Thông báo không tồn tại."

    try:
        print(f"Gửi email tới {recipient_email} cho noti_id = {noti_id}")
        print(notification.noti_title, notification.noti_message)

        # Tạo nội dung email
        msg = Message(
            subject=f"[🔥Cảnh báo] {notification.noti_title}",
            recipients=[recipient_email],
            html=f"""
                <h3>{notification.noti_title}</h3>
                <p>{notification.noti_message}</p>
                <p><i>Gửi lúc: {notification.noti_create_at.strftime('%Y-%m-%d %H:%M:%S')}</i></p>
            """
        )
        mail.send(msg)

        # 🛡️ Kiểm tra nếu đã có bản ghi, xóa trước để ghi lại
        existing = NotificationPlatform.query.filter_by(noti_id=noti_id, plat_id=1).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        # ✅ Ghi bản ghi mới vào notification_platforms
        record = NotificationPlatform(
            noti_id=noti_id,
            plat_id=1,  # Email platform
            np_status=True,
            np_sent_at=datetime.utcnow(),
            np_recipient_address=recipient_email,
            np_retry_count=0
        )
        db.session.add(record)
        db.session.commit()

        return True, "Email gửi thành công."

    except Exception as e:
        db.session.rollback()  # 🧯 Quan trọng! Khôi phục session nếu lỗi
        db.session.add(NotificationPlatform(
            noti_id=noti_id,
            plat_id=1,
            np_status=False,
            np_sent_at=datetime.utcnow(),
            np_error_message=str(e),
            np_recipient_address=recipient_email,
            np_retry_count=1
        ))
        db.session.commit()
        return False, f"Gửi thất bại: {str(e)}"
