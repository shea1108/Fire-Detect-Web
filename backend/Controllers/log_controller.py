# backend/Controllers/log_controller.py
import base64
import io
import os
import time
import uuid
from PIL import Image, ImageDraw, ImageFont
from backend.Models import db, Log
from backend.Models.log_bboxes_model import LogBBox
from backend.Models.devices_model import Device
from backend.utils.models_manager import model_manager

last_log_times = {}  # cooldown theo thiết bị

def handle_detect_from_api(data):
    try:
        image_b64 = data.get("image")
        model_id = data.get("model_id")
        dev_id = data.get("dev_id")

        if not image_b64 or not model_id or not dev_id:
            return False, "Thiếu image / model_id / dev_id"

        # Decode ảnh
        header, encoded = image_b64.split(",", 1)
        image_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')

        model = model_manager.get_model(model_id)
        if not model:
            return False, f"Không load được model ID {model_id}"

        # Nhận diện
        results = model(image, conf=0.25, iou=0.45, verbose=False)
        detections, fire_detections = [], []

        for result in results:
            for box in result.boxes.data.tolist():
                if len(box) >= 6:
                    x1, y1, x2, y2, score, cls = box
                    label = model.names.get(int(cls), 'unknown')
                    det = {'bbox': [x1, y1, x2, y2], 'confidence': score, 'label': label}
                    detections.append(det)
                    if label.lower() == 'fire':
                        fire_detections.append(det)

        if not fire_detections:
            return True, {"detections": detections, "message": "Không phát hiện cháy"}

        # Kiểm tra cooldown
        now = time.time()
        if now - last_log_times.get(dev_id, 0) < 3:
            return True, {"detections": detections, "message": "Cooldown, chưa ghi log"}

        # Lưu ảnh gốc và bbox
        save_dir = os.path.join('static', 'log_images', str(dev_id))
        os.makedirs(save_dir, exist_ok=True)

        new_log = Log(dev_id=dev_id, model_id=model_id)
        db.session.add(new_log)
        db.session.flush()

        log_id = new_log.log_id
        origin_path = os.path.join(save_dir, f"{log_id}_origin_model{model_id}_dev{dev_id}.jpg")
        bbox_path   = os.path.join(save_dir, f"{log_id}_bbox_model{model_id}_dev{dev_id}.jpg")

        image_origin = image.copy()
        bbox_image = image.copy()
        draw = ImageDraw.Draw(bbox_image)
        try:
            font = ImageFont.truetype("arial.ttf", 15)
        except IOError:
            font = ImageFont.load_default()

        for det in fire_detections:
            bbox, confidence = det['bbox'], det['confidence']
            draw.rectangle(bbox, outline="red", width=3)
            draw.text((bbox[0], bbox[1] - 15), f"Fire: {confidence*100:.1f}%", fill="red", font=font)

        image_origin.save(origin_path)
        bbox_image.save(bbox_path)
        new_log.log_image_path = origin_path.replace("\\", "/")

        # Lưu bbox vào LogBBox
        for det in fire_detections:
            x1, y1, x2, y2 = det['bbox']
            width, height = x2 - x1, y2 - y1
            db.session.add(LogBBox(
                log_id=log_id,
                confidence=float(det['confidence']),
                x_center=x1 + width/2,
                y_center=y1 + height/2,
                width=width,
                height=height
            ))

        db.session.commit()
        last_log_times[dev_id] = now

        return True, {"detections": detections, "message": "Đã lưu log", "log_id": log_id}

    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi xử lý: {e}"
