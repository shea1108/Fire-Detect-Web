# backend/Controllers/mail_controller.py
from flask import current_app
from flask_mail import Message
from backend.extensions import mail, db
from backend.Models.notification_models_model import NotificationPlatform
from datetime import datetime
from zoneinfo import ZoneInfo

from email.utils import format_datetime



def send_email(subject: str, html_body: str, recipient_email: str, noti_id: int = None):
    if not current_app.config.get("MAIL_ENABLED", True):
        print("🚫 Gửi email đã bị tắt (MAIL_ENABLED=False)")
        return True, "Gửi email đã bị tắt"

    try:
        # Gửi email
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            html=html_body
        )
        #msg.date = format_datetime(datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")))

        mail.send(msg)
        print(f"✅ Đã gửi email đến {recipient_email}")

        if noti_id:
            existing_log = NotificationPlatform.query.filter_by(noti_id=noti_id, plat_id=1).first()
            if existing_log:
                # Cập nhật log nếu đã tồn tại
                existing_log.np_status = True
                existing_log.np_sent_at = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))

                existing_log.np_error_message = None
                existing_log.np_retry_count = 0
                existing_log.np_recipient_address = recipient_email
            else:
                # Tạo mới nếu chưa tồn tại
                db.session.add(NotificationPlatform(
                    noti_id=noti_id,
                    plat_id=1,
                    np_status=True,
                    np_sent_at=datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")),
                    np_recipient_address=recipient_email,
                    np_retry_count=0
                ))
            db.session.commit()

        return True, "✅ Email đã gửi thành công"

    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")

        if noti_id:
            db.session.rollback()  # rollback nếu trước đó có lỗi
            existing_log = NotificationPlatform.query.filter_by(noti_id=noti_id, plat_id=1).first()
            if existing_log:
                existing_log.np_status = False
                existing_log.np_sent_at = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
                existing_log.np_error_message = str(e)
                existing_log.np_retry_count += 1
                existing_log.np_recipient_address = recipient_email
            else:
                db.session.add(NotificationPlatform(
                    noti_id=noti_id,
                    plat_id=1,
                    np_status=False,
                    np_sent_at=datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
,
                    np_error_message=str(e),
                    np_recipient_address=recipient_email,
                    np_retry_count=1
                ))
            db.session.commit()

        return False, f"Gửi thất bại: {str(e)}"
