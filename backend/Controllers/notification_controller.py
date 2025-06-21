# backend/Controllers/notification_controller.py
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import current_app
from flask_mail import Message

from backend.Models import db
from backend.Models.notifications_model import Notification
from backend.Models.logs_model import Log
from backend.Models.devices_model import Device
from backend.Controllers.mail_controller import send_email, mail


def create_notification(log_id: int):
    log = Log.query.get(log_id)
    if not log:
        return None, "Log không tồn tại"

    device = Device.query.get(log.dev_id)
    device_name = device.dev_name if device else "Không rõ thiết bị"
    timestamp = log.log_create_at.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).strftime('%H:%M:%S %d-%m-%Y')

    notification = Notification(
        log_id=log_id,
        noti_title=f"Phát hiện cháy tại thiết bị {device_name}",
        noti_message=f"Hệ thống phát hiện cháy tại thiết bị {device_name} vào lúc {timestamp}",
        noti_is_receive=False
    )

    try:
        db.session.add(notification)
        db.session.commit()
        return notification, None
    except Exception as e:
        db.session.rollback()
        return None, f"Lỗi tạo notification: {e}"

def send_email_notification(noti_id: int, recipient_email: str, user_name="Người dùng", origin_path=None, bbox_path=None):
    # SỬA 1: Thêm origin_path=None, bbox_path=None vào chữ ký hàm
    
    notification = Notification.query.get(noti_id)
    if not notification:
        return False, "Không tìm thấy thông báo"

    log = notification.log
    device = Device.query.get(log.dev_id)
    device_name = device.dev_name if device else "Không rõ thiết bị"
    timestamp = log.log_create_at.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).strftime('%H:%M:%S %d-%m-%Y')
    year = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).year

    # SỬA 2: Sử dụng trực tiếp origin_path và bbox_path được truyền vào.
    # Không cần tính toán lại đường dẫn nữa vì nó đã được cung cấp chính xác.
    # Các đường dẫn này là đường dẫn vật lý đầy đủ, ví dụ: "frontend/static/log_images/..."
    
    # ✅ Nếu thiếu 1 trong 2 ảnh thì KHÔNG gửi email
    if not origin_path or not bbox_path or not os.path.exists(origin_path) or not os.path.exists(bbox_path):
        print(f"⚠️ Không gửi email vì thiếu file ảnh hoặc đường dẫn không tồn tại.")
        print(f"   -> Đang tìm kiếm tại: {origin_path} và {bbox_path}")
        return False, "Thiếu ảnh đính kèm, không gửi email"

    # Tiêu đề và nội dung HTML (GIỮ NGUYÊN NHƯ CŨ)
    subject = f"[🔥 Fire Alert] Thiết bị {device_name} phát hiện cháy"
    html_body = f"""
        <table style="width:100%; max-width:600px; margin:0 auto; font-family:Arial,sans-serif; background:#fff; padding:20px; border-radius:8px; border:1px solid #eee;">
            <tr>
                <td style="text-align:center;">
                    <h2 style="color:#d90429;">🔥 CẢNH BÁO CHÁY</h2>
                    <p style="color:#444;">Hệ thống phát hiện cháy từ thiết bị <strong>{device_name}</strong></p>
                </td>
            </tr>
            <tr>
                <td>
                    <p>Xin chào <strong>{user_name}</strong>,</p>
                    <p>Lúc <strong>{timestamp}</strong>, hệ thống đã ghi nhận dấu hiệu cháy từ thiết bị <strong>{device_name}</strong>.</p>
                    <p>2 hình ảnh được đính kèm trong email này gồm:</p>
                    <ul>
                        <li><strong>Ảnh gốc</strong>: Chụp từ camera ngay thời điểm phát hiện</li>
                        <li><strong>Ảnh BBox</strong>: Hiển thị vùng nghi ngờ cháy đã được AI nhận diện</li>
                    </ul>
                    <p style="margin-top: 20px;">Vui lòng kiểm tra lại khu vực liên quan và liên hệ lực lượng chức năng nếu xác nhận là cháy thật.</p>
                    <br/>
                    <p style="color:gray;">Đây là email tự động từ hệ thống FireDetect.</p>
                    <p>Trân trọng,<br/>Đội ngũ FireDetect</p>
                </td>
            </tr>
            <tr>
                <td style="text-align:center; font-size:12px; color:#888; padding-top:30px;">
                    &copy; {year} FireDetect. All rights reserved.
                </td>
            </tr>
        </table>
    """

    try:
        msg = Message(subject=subject, recipients=[recipient_email], html=html_body)

        # SỬA 3: Đổi tên biến để khớp với logic đính kèm file của bạn
        for abs_path in [origin_path, bbox_path]:
            with open(abs_path, 'rb') as f:
                filename = os.path.basename(abs_path)
                msg.attach(filename, "image/jpeg", f.read())

        mail.send(msg)
        print(f"[📧 EMAIL] Email đã gửi thành công tới {recipient_email}")
        return True, "📧 Email đã gửi thành công"

    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        return False, f"Lỗi gửi email: {str(e)}"
