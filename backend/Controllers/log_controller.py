from flask_socketio import SocketIO, emit
import base64, uuid, time
from io import BytesIO
from PIL import Image
from backend.Models import db, Log
from backend.extensions import socketio



# Biến lưu thời điểm log cuối cùng theo device
last_log_times = {}

@socketio.on('frame')
def handle_frame(data):
    data_url = data.get("image")
    dev_id = data.get("dev_id")  
    model_id = data.get("model_id")  

    if not data_url or not dev_id or not model_id:
        return

    # Decode base64 ảnh
    header, encoded = data_url.split(",", 1)
    image_data = base64.b64decode(encoded)

    # Tạo ảnh từ dữ liệu
    image_id = str(uuid.uuid4())
    image_path = f'static/uploads/{image_id}.jpg'
    with open(image_path, 'wb') as f:
        f.write(image_data)

    # Detect lửa
    detections = detect_fire(image_path)

    emit('detections', {
        'detections': [
            {'bbox': bbox, 'confidence': confidence}
            for bbox, confidence in detections
        ]
    })

    # Nếu có phát hiện lửa
    if detections:
        confidence = detections[0][1]

        now = time.time()
        last_time = last_log_times.get(dev_id, 0)

        # Chỉ log nếu vượt qua thời gian chờ (vd: 10 giây)
        if now - last_time > 5:
            log = Log(
                log_id=str(uuid.uuid4()),
                dev_id=dev_id,
                model_id=model_id,
                log_fire_confidence=confidence,
                log_image_path=image_path
            )
            db.session.add(log)
            db.session.commit()
            last_log_times[dev_id] = now


def save_fire_log(dev_id, model_id, confidence, image_path, cooldown_seconds=5):
    now = time.time()
    last_time = last_log_times.get(dev_id, 0)

    if now - last_time < cooldown_seconds:
        return False  # Chưa đủ thời gian giãn cách

    # Tạo và lưu log
    log = Log(
        log_id=str(uuid.uuid4()),
        dev_id=dev_id,
        model_id=model_id,
        log_fire_confidence=confidence,
        log_image_path=image_path
    )
    db.session.add(log)
    db.session.commit()

    last_log_times[dev_id] = now
    return True