from flask_socketio import SocketIO, emit
import base64, uuid, time
from PIL import Image
from backend.Models import db, Log
from backend.extensions import socketio
from backend.Models.devices_model import Device

# Biến lưu thời điểm log cuối cùng theo device
last_log_times = {}

@socketio.on('frame')
def handle_frame(data):
    data_url = data.get("image")
    dev_name = data.get("dev_name")  # nhận dev_name thay vì dev_id
    user_id = data.get("user_id")
    model_id = data.get("model_id")

    if not data_url or not dev_name or not user_id or not model_id:
        print("❌ Thiếu dữ liệu từ client")
        return

    # Lấy thiết bị từ DB
    device = Device.query.filter_by(dev_name=dev_name, user_id=user_id).first()
    if not device:
        print(f"❌ Device '{dev_name}' của user {user_id} không tồn tại")
        return

    # ✅ Lấy dev_id thực từ DB
    dev_id = device.dev_id
    print("👉 dev_id value and type:", dev_id, type(dev_id))

    # Kiểm tra kiểu dev_id
    if not isinstance(dev_id, int):
        print(f"❌ dev_id không hợp lệ: {dev_id}")
        return

    # Decode ảnh
    header, encoded = data_url.split(",", 1)
    image_data = base64.b64decode(encoded)

    # Lưu ảnh
    image_id = str(uuid.uuid4())
    image_path = f'static/uploads/{image_id}.jpg'
    with open(image_path, 'wb') as f:
        f.write(image_data)

    # Detect lửa
    detections = detect_fire(image_path)

    # Emit kết quả detect về client
    emit('detections', {
        'detections': [
            {'bbox': bbox, 'confidence': confidence}
            for bbox, confidence in detections
        ]
    })

    # Nếu có lửa thì lưu log
    if detections:
        confidence = detections[0][1]

        now = time.time()
        last_time = last_log_times.get(dev_id, 0)

        if now - last_time > 5:  # cooldown 5 giây
            try:
                log = Log(
                    dev_id=dev_id,  # ✅ đúng kiểu int
                    model_id=model_id,
                    log_fire_confidence=confidence,
                    log_image_path=image_path
                )
                db.session.add(log)
                db.session.commit()
                last_log_times[dev_id] = now
                print(f"✅ Log saved for dev_id {dev_id}")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error saving fire detection log to database: {e}")

def save_fire_log(dev_id, model_id, confidence, image_path, cooldown_seconds=5):
    if not isinstance(dev_id, int):
        print(f"❌ save_fire_log: dev_id không phải int: {dev_id}")
        return False

    now = time.time()
    last_time = last_log_times.get(dev_id, 0)

    if now - last_time < cooldown_seconds:
        return False

    try:
        log = Log(
            dev_id=dev_id,  # ✅ dùng dev_id đúng kiểu
            model_id=model_id,
            log_fire_confidence=confidence,
            log_image_path=image_path
        )
        db.session.add(log)
        db.session.commit()
        last_log_times[dev_id] = now
        print(f"✅ save_fire_log: Log saved for dev_id {dev_id}")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ save_fire_log: lỗi khi ghi log: {e}")
        return False
