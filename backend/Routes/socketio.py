from flask_socketio import emit
from PIL import Image
import base64, io, uuid, os, json
from ultralytics import YOLO
from backend.Controllers.log_controller import save_fire_log  
from datetime import datetime  
from backend.Models import db, Log

model = YOLO('Yolo/best.pt')

def register_socketio(socketio):
    @socketio.on('frame')
    def handle_frame(data):
        # ✅ Xử lý data đầu vào linh hoạt
        if isinstance(data, str):
            data = data.strip()
            if data.startswith('data:image/jpeg;base64,') or data.startswith('data:image/png;base64,'):
                # Nếu là chuỗi base64 ảnh thẳng, tạo dict giả định
                image_b64 = data
                dev_id = 'test-device'
                model_id = 'test-model'
                # tạo dict giả để dùng sau
                data = {
                    'image': image_b64,
                    'dev_id': dev_id,
                    'model_id': model_id
                }
            elif data.startswith('{'):
                # Nếu là JSON string thì parse
                try:
                    data = json.loads(data)
                except Exception as e:
                    print("❌ Lỗi parse JSON từ frame:", e)
                    return
            else:
                print("❌ Dữ liệu nhận được không phải JSON hoặc base64 image:", repr(data[:50]))
                return

        image_b64 = data.get('image', '')
        if not image_b64 or ',' not in image_b64:
            print("❌ Không tìm thấy dữ liệu ảnh hợp lệ.")
            return

        try:
            # Tách và decode base64 image
            image_data = base64.b64decode(image_b64.split(',')[1])
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
        except Exception as e:
            print("❌ Lỗi xử lý ảnh:", e)
            return

        # Lưu ảnh tạm để debug hoặc phục vụ xử lý sau
        image_id = str(uuid.uuid4())
        save_path = f'static/uploads/{image_id}.jpg'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        image.save(save_path)

        # 🔍 Detect fire với YOLO model
        try:
            results = model(image)
        except Exception as e:
            print("❌ Lỗi khi chạy mô hình YOLO:", e)
            return

        detections = []
        for result in results:
            for box in result.boxes.data.tolist():
                x1, y1, x2, y2, score, cls = box
                label = model.names[int(cls)]
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': float(score),
                    'class_id': int(cls),
                    'label': label
                })

                # Nếu phát hiện 'fire' thì gọi lưu log
                if label.lower() == 'fire':
                    dev_id = data.get('dev_id', 'test-device')
                    model_id = data.get('model_id', 'test-model')
                    save_fire_log(dev_id, model_id, float(score), save_path)

        # Gửi kết quả phát hiện về client
        emit('detections', {'detections': detections})

    @socketio.on('save_log')
    def handle_save_log(data):
        # Parse JSON nếu nhận chuỗi
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception as e:
                print("❌ Lỗi parse JSON từ save_log:", e)
                return

        confidence = data.get('confidence')
        base64_image = data.get('base64Image')
        dev_id = data.get('dev_id')
        model_id = data.get('model_id')

        if not all([confidence, base64_image, dev_id, model_id]):
            print("❌ Thiếu dữ liệu đầu vào trong save_log")
            return

        try:
            # Lưu ảnh log
            image_data = base64.b64decode(base64_image.split(',')[1])
            filename = f"saved_frame_{uuid.uuid4().hex}.jpg"
            filepath = os.path.join('static', 'log_images', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            print("❌ Lỗi khi lưu ảnh log:", e)
            return

        try:
            # Tạo log mới và commit vào DB
            log_id = str(uuid.uuid4())
            new_log = Log(
                log_id=log_id,
                dev_id=dev_id,
                model_id=model_id,
                log_fire_confidence=confidence,
                log_image_path=filepath
            )
            db.session.add(new_log)
            db.session.commit()
            print(f"[LOG SAVED] {log_id}")
        except Exception as e:
            print("❌ Lỗi khi lưu log vào cơ sở dữ liệu:", e)
