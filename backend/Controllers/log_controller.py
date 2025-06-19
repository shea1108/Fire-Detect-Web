# backend/Controllers/log_controller.py

from backend.socket.common import perf_monitor  # THÊM import

import os
import io
import base64
import time
import logging
import threading
from PIL import Image, ImageDraw, ImageFont

from flask import current_app, session, has_request_context
from backend.Models.users_model import User
from backend.extensions import socketio

from backend.Models import db, Log
from backend.Models.log_bboxes_model import LogBBox
from backend.utils.models_manager import model_manager
from backend.services.log_noti_send_email import handle_post_log_events


last_log_times = {}

def trigger_notification_in_background(app, log_id, user_email, user_name):

    with app.app_context():
        try:
            ok, msg, noti_id = handle_post_log_events(log_id, user_email, user_name)
            
            if ok:
                logging.info(f"Gửi thông báo thành công cho log_id: {log_id} tới {user_email}.")
            else:
                logging.warning(f"Gửi thông báo thất bại cho log_id: {log_id}. Lý do: {msg}")

        except Exception as e:
            logging.error(
                f"Lỗi không xác định trong tác vụ nền cho log_id: {log_id}. Lỗi: {e}", 
                exc_info=True  
            )


def handle_detect_from_api(data):
    current_thread_info = threading.current_thread()
    logging.info(f"[MAIN] Request này đang được xử lý trên luồng: {current_thread_info}")
    
    dev_id = data.get("dev_id")
    logging.info(f"[MAIN] Bắt đầu xử lý frame từ dev_id: {dev_id}")
    try:
        image_b64 = data.get("image")
        model_id = data.get("model_id")
        dev_id = data.get("dev_id")

        if not image_b64 or not model_id or not dev_id:
            return False, "Thiếu image / model_id / dev_id"

        # Decode ảnh base64
        try:
            header, encoded = image_b64.split(",", 1)
            image_data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
        except Exception as e:
            return False, f"Lỗi giải mã ảnh: {e}"

        # 📌 Bắt đầu đo thời gian
        start_time = time.time()


        # Load mô hình
        model = model_manager.get_model(model_id)
        if not model:
            return False, f"Không load được model ID {model_id}"

        # Thực hiện nhận diện
        results = model(image, conf=0.25, iou=0.45, verbose=False)

        # 📌 Kết thúc đo thời gian
        end_time = time.time()
        elapsed = end_time - start_time
        fps = 1.0 / elapsed if elapsed > 0 else 0
        perf_monitor.last_fps = fps  # ✅ Cập nhật thật sự từ YOLO
        logging.info(f"⚙️ Stats - dev_id: {dev_id}, FPS: {fps:.2f}, Time: {elapsed:.3f}s")


        detections, fire_detections = [], []

        for result in results:
            for box in result.boxes.data.tolist():
                if len(box) >= 6:
                    x1, y1, x2, y2, score, cls = box
                    label = model.names.get(int(cls), 'unknown')
                    det = {
                        'bbox': [x1, y1, x2, y2],
                        'confidence': score,
                        'label': label
                    }
                    detections.append(det)
                    if label.lower() == 'fire':
                        fire_detections.append(det)

        if not fire_detections:
            return True, {"detections": detections, "message": "Không phát hiện cháy"}

        # Cooldown theo thiết bị
        now = time.time()
        if now - last_log_times.get(dev_id, 0) < 0.3:
            logging.info(f"!!! BỎ QUA DO COOLDOWN 0.3 GIÂY CHO dev_id: {dev_id} !!!")
            return True, {"detections": detections, "message": "Cooldown, chưa ghi log"}

        # Lưu ảnh
        save_dir = os.path.join('static', 'log_images', str(dev_id))
        os.makedirs(save_dir, exist_ok=True)

        new_log = Log(dev_id=dev_id, model_id=model_id)
        db.session.add(new_log)
        db.session.flush()  # Để có log_id

        log_id = new_log.log_id
        origin_path = os.path.join(save_dir, f"{log_id}_origin_model{model_id}_dev{dev_id}.jpg")
        bbox_path = os.path.join(save_dir, f"{log_id}_bbox_model{model_id}_dev{dev_id}.jpg")

        image_origin = image.copy()
        bbox_image = image.copy()
        draw = ImageDraw.Draw(bbox_image)

        try:
            font = ImageFont.truetype("arial.ttf", 15)
        except IOError:
            font = ImageFont.load_default()

        for det in fire_detections:
            x1, y1, x2, y2 = det['bbox']
            confidence = det['confidence']
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
            draw.text((x1, y1 - 15), f"Fire: {confidence*100:.1f}%", fill="red", font=font)

        image_origin.save(origin_path)
        bbox_image.save(bbox_path)
        new_log.log_image_path = origin_path.replace("\\", "/")

        # Lưu bbox
        for det in fire_detections:
            x1, y1, x2, y2 = det['bbox']
            width, height = x2 - x1, y2 - y1
            db.session.add(LogBBox(
                log_id=log_id,
                confidence=float(det['confidence']),
                x_center=x1 + width / 2,
                y_center=y1 + height / 2,
                width=width,
                height=height
            ))

        db.session.commit()
        last_log_times[dev_id] = now

        if has_request_context() and "user_id" in session:
            user_id = session['user_id']
            user = User.query.get(user_id)
            
            # Nếu tìm thấy user, lấy thông tin và kích hoạt tác vụ nền
            if user:
                app_context = current_app._get_current_object()
                user_email = user.user_email
                user_name = user.user_name
                
                logging.info(f"[MAIN] Chuẩn bị kích hoạt tác vụ nền cho log_id: {log_id} tới user: {user_email}")
                socketio.start_background_task(
                    target=trigger_notification_in_background, 
                    app=app_context, 
                    log_id=log_id,
                    user_email=user_email, # Truyền email
                    user_name=user_name   # Truyền tên
                )
                logging.info(f"[MAIN] Đã kích hoạt. Trả về response cho client NGAY BÂY GIỜ.")
            else:
                logging.warning(f"⚠️ Không tìm thấy user với user_id: {user_id} trong DB. Không gửi thông báo.")
        else:
            logging.warning("⚠️ Không gửi thông báo vì không có session (chưa đăng nhập)")

        return True, {"detections": detections, "message": "Đã lưu log", "log_id": log_id}

    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi xử lý: {e}"