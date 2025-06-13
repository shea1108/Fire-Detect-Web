# backend/Controllers/notification_controller.py
from backend.Controllers.mail_controller import send_email
from backend.Models.notifications_model import Notification

def send_email_notification(noti_id: int, recipient_email: str):
    notification = Notification.query.get(noti_id)
    if not notification:
        return False, "Không tìm thấy thông báo"

    subject = f"[🔥 Cảnh báo] {notification.noti_title}"
    html_body = f"""
        <h3>{notification.noti_title}</h3>
        <p>{notification.noti_message}</p>
        <p><i>Gửi lúc: {notification.noti_create_at.strftime('%Y-%m-%d %H:%M:%S')}</i></p>
    """

    return send_email(subject, html_body, recipient_email, noti_id)
