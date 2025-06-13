# # backend/socket/notify_utils.py
# from backend.Models.notifications_model import Notification
# from backend.Models.devices_model import Device
# from backend.Models.logs_model import Log
# from backend.extensions import db
# from datetime import datetime
# import logging

# logger = logging.getLogger(__name__)

# def create_notification_for_log(log_id):
#     log = Log.query.get(log_id)
#     if not log:
#         return None, "Log không tồn tại"

#     device = Device.query.get(log.dev_id)
#     device_name = device.dev_name if device else "Không rõ thiết bị"
#     timestamp = log.log_create_at.strftime('%H:%M:%S %d-%m-%Y')

#     notification = Notification(
#         log_id=log_id,
#         noti_title=f"Phát hiện cháy tại thiết bị {device_name}",
#         noti_message=f"Hệ thống phát hiện cháy tại thiết bị {device_name} vào lúc {timestamp}",
#         noti_is_receive=False
#     )
#     try:
#         db.session.add(notification)
#         db.session.commit()
#         return notification, None
#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"❌ Lỗi tạo notification: {e}")
#         return None, str(e)



# from backend.Controllers.mail_controller import send_email
# from backend.Models.devices_model import Device
# from datetime import datetime

# def send_fire_notification_email(notification, recipient_email, user_name="Người dùng"):
#     log = notification.log
#     device = Device.query.get(log.dev_id)
#     device_name = device.dev_name if device else "Không rõ thiết bị"
#     timestamp = log.log_create_at.strftime('%H:%M:%S %d-%m-%Y')
#     year = datetime.utcnow().year

#     origin_image_url = f"http://localhost:5000/{log.log_image_path}"
#     bbox_image_url = origin_image_url.replace("_origin_", "_bbox_")

#     subject = f"[🔥 Fire Alert] Thiết bị {device_name} phát hiện cháy"
#     html_body = f'''
#         <table style="width:100%; max-width:600px; margin:0 auto; font-family:Arial,sans-serif; background:#f9f9f9; padding:20px; border-radius:8px;">
#             <tr><td style="text-align:center;"><h2 style="color:#e63946;">🔥 Cảnh báo phát hiện cháy</h2></td></tr>
#             <tr><td>
#                 <p>Xin chào <strong>{user_name}</strong>,</p>
#                 <p>Phát hiện cháy tại thiết bị <strong>{device_name}</strong> lúc <strong>{timestamp}</strong>.</p>
#                 <p>Dưới đây là ảnh phát hiện:</p>

#                 <div style="margin:20px 0;"><p><b>Ảnh gốc:</b></p><img src="{origin_image_url}" style="max-width:100%; border-radius:8px; border:1px solid #ccc;" /></div>
#                 <div style="margin:20px 0;"><p><b>Ảnh bbox:</b></p><img src="{bbox_image_url}" style="max-width:100%; border-radius:8px; border:1px solid #ccc;" /></div>

#                 <p style="margin-top:20px;">Vui lòng kiểm tra khu vực và liên hệ khẩn nếu cần.</p>
#                 <p>Trân trọng,<br />Đội ngũ FireDetect</p>
#             </td></tr>
#             <tr><td style="text-align:center; font-size:12px; color:#888; padding-top:30px;">&copy; {year} FireDetect</td></tr>
#         </table>
#     '''

#     return send_email(subject, html_body, recipient_email, noti_id=notification.noti_id)
