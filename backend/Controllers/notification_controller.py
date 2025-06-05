from flask import current_app
from flask_mail import Message
from backend.extensions import mail, db
from backend.Models.notifications_model import Notification
from backend.Models.notification_models_model import NotificationPlatform
from datetime import datetime


def send_email_notification(noti_id: int, recipient_email: str):
    if not MAIL_ENABLED:
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

        # Gửi email
        mail.send(msg)

        # Lưu log vào bảng notification_platforms
        record = NotificationPlatform(
            noti_id=noti_id,
            plat_id=1,  # Giả định 1 là Email
            np_status=True,
            np_sent_at=datetime.utcnow(),
            np_recipient_address=recipient_email,
            np_retry_count=0
        )
        db.session.add(record)
        db.session.commit()

        return True, "Email gửi thành công."

    except Exception as e:
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
