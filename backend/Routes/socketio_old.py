#backend/Routes/socketio.py

# ==============================================================================
# PHẦN 1: IMPORTS VÀ CẤU HÌNH BAN ĐẦU
# ==============================================================================
import base64
import io
import json
import logging
import os
import time
import uuid

import numpy as np
import torch

from backend.Models import Log, db
from backend.Models.devices_model import Device
from backend.Models.models_model import Model as ModelDB
from backend.Models.log_bboxes_model import  db, LogBBox
from collections import deque

from flask import request, session
from flask_socketio import emit
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

from backend.utils.models_manager import model_manager # Giả sử bạn import từ đây


# Cấu hình logging để theo dõi hoạt động
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ==============================================================================
# PHẦN 2: BỘ QUẢN LÝ MODEL ĐỘNG
# ==============================================================================
class ModelManager:
    def __init__(self):
        self.loaded_models = {}
        logger.info("🤖 ModelManager is initialized and ready.")

    def get_model(self, model_id):
        try:
            model_id = int(model_id)
        except (ValueError, TypeError):
            logger.error(f"❌ Invalid model_id format: {model_id}.")
            return None

        if model_id in self.loaded_models:
            return self.loaded_models[model_id]

        logger.info(f"Model ID {model_id} not in cache. Querying database...")
        model_record = ModelDB.query.get(model_id)

        if not model_record or not model_record.model_path:
            logger.error(f"❌ No record/path in DB for ID: {model_id}")
            return None

        model_path = model_record.model_path
        if not os.path.exists(model_path):
            logger.error(f"❌ Model file not found at: '{model_path}'")
            return None

        try:
            logger.info(f"Loading model from: '{model_path}'...")
            model = YOLO(model_path)

            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {device}")
            model.to(device)

            self.loaded_models[model_id] = model
            logger.info(f"👍 Successfully loaded and cached model ID {model_id}.")
            return model
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model from '{model_path}': {e}")
            return None

# Khởi tạo một thực thể duy nhất của ModelManager
model_manager = ModelManager()


# ==============================================================================
# PHẦN 3: CÁC LỚP VÀ HÀM TIỆN ÍCH
# ==============================================================================
class PerformanceMonitor:
    def __init__(self):
        self.frame_count = 0
        self.detection_count = 0
        self.start_time = None
        self.last_log_time = time.time()
        self.log_interval = 5
        self.total_data_received = 0  # Tổng byte ảnh đã nhận
        self.total_recv_time = 0      # Tổng thời gian giải mã base64
        self.timestamps = deque(maxlen=30)  # Sliding window 30 frames

    def update(self, detections_count, data_size_kb=None, recv_time=None):
        self.timestamps.append(time.time())
        if self.start_time is None: self.start_time = time.time()
        self.frame_count += 1
        self.detection_count += detections_count
        if data_size_kb and recv_time:
            self.total_data_received += data_size_kb
            self.total_recv_time += recv_time
        if time.time() - self.last_log_time >= self.log_interval:
            self.log_stats()
            self.last_log_time = time.time()


    def log_stats(self):
        stats = self.get_stats()
        if stats:
            logger.info(f"Performance - Frames: {stats.get('frames_processed', 0)}, Detections: {stats.get('total_detections', 0)}, FPS: {stats.get('fps', 0):.2f}")

    def get_stats(self):
        if self.start_time is None:
            return {}

        # FPS theo sliding window 30 frame
        if len(self.timestamps) >= 2:
            elapsed_window = self.timestamps[-1] - self.timestamps[0]
            fps_sliding = (len(self.timestamps) - 1) / elapsed_window if elapsed_window > 0 else 0
        else:
            fps_sliding = 0

        # Tốc độ mạng trung bình (KB/s)
        avg_speed = (self.total_data_received / self.total_recv_time) if self.total_recv_time > 0 else 0

        return {
            'frames_processed': self.frame_count,
            'total_detections': self.detection_count,
            'fps': round(fps_sliding, 2),  # sử dụng sliding FPS thay vì toàn thời gian
            'avg_network_speed_kbps': round(avg_speed, 2)
        }



perf_monitor = PerformanceMonitor()
last_log_times = {}

# --- CÁC HÀM TIỆN ÍCH MỚI ĐỂ TRÁNH LẶP CODE ---
def _get_device_from_hardware_id(hw_id):
    """Lấy thông tin thiết bị từ DB bằng hardware ID của nó."""
    if not hw_id:
        return None
    return Device.query.filter_by(dev_hardware_id=hw_id).first()



def _save_detection_log(dev_id, model_id, orig_image, bbox_image, detections, cooldown_seconds=3):
    if not detections:
        logger.info("🚫 Bỏ qua log vì không có fire detection.")
        return False
    if not isinstance(dev_id, int): return False
    now = time.time()
    if now - last_log_times.get(dev_id, 0) < cooldown_seconds:
        logger.info(f"Log skipped for device {dev_id} due to cooldown.")
        return False

    try:
        # 1. Tạo bản ghi log sơ bộ (chưa có path ảnh)
        new_log = Log(dev_id=dev_id, model_id=model_id)
        db.session.add(new_log)
        db.session.flush()  # Lấy log_id

        log_id = new_log.log_id
        save_dir = os.path.join('static', 'log_images', str(dev_id))
        os.makedirs(save_dir, exist_ok=True)

        # 2. Tạo tên file theo định dạng yêu cầu
        origin_filename = f"{log_id}_origin_model{model_id}_dev{dev_id}.jpg"
        bbox_filename   = f"{log_id}_bbox_model{model_id}_dev{dev_id}.jpg"

        origin_path = os.path.join(save_dir, origin_filename)
        bbox_path = os.path.join(save_dir, bbox_filename)

        # 3. Lưu cả 2 ảnh
        orig_image.save(origin_path)
        bbox_image.save(bbox_path)

       # 4. Cập nhật lại log_image_path (chuẩn hóa dấu /)
        new_log.log_image_path = origin_path.replace("\\", "/")


        # 5. Lưu các bbox
        for det in detections:
            bbox = det.get('bbox')
            confidence = det.get('confidence')
            if not bbox or confidence is None: continue
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1

            db.session.add(LogBBox(
                log_id=log_id,
                confidence=float(confidence),
                x_center=x1 + width / 2,
                y_center=y1 + height / 2,
                width=width,
                height=height
            ))

        db.session.commit()
        last_log_times[dev_id] = now
        logger.info(f"✅ Log {log_id} saved. Images: origin + bbox.")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error saving log: {e}")
        return False

# ==============================================================================
# PHẦN 4: ĐĂNG KÝ CÁC SỰ KIỆN SOCKET.IO
# ==============================================================================
def register_socketio(socketio):

    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        emit('status', {'message': 'Connected to fire detection server'})

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")

    @socketio.on('get_models')
    def handle_get_models():
        user_id = session.get('user_id')
        models = []
        
        try:
            if user_id:
                logger.info(f"User '{session.get('user_name')}' requested models. Getting all active models.")
                models = ModelDB.query.filter_by(model_status=True).order_by(ModelDB.model_name).all()
            else:
                logger.info("Guest user requested models. Getting the default model.")
                first_model = ModelDB.query.filter_by(model_status=True).first()
                if first_model:
                    models = [first_model] # Trả về một danh sách chỉ chứa một model

            if not models:
                emit('models_list', {'status': 'error', 'message': 'Không tìm thấy model nào hoạt động.'})
                return

            models_list = [{"model_id": m.model_id, "model_name": m.model_name} for m in models]
            emit('models_list', {'status': 'success', 'models': models_list})
            logger.info(f"Sent {len(models_list)} model(s) to the client.")

        except Exception as e:
            logger.error(f"Error in handle_get_models: {e}")
            emit('models_list', {'status': 'error', 'message': 'Lỗi server khi tải model.'})

    @socketio.on('save_device')
    def handle_save_device(data):

        user_id = session.get('user_id') 
        
        dev_name = data.get('dev_name')
        client_hardware_id = data.get('dev_hardware_id') 

        if user_id is None:
            logger.warning(f"Guest user is saving device: HW ID '{client_hardware_id}'")

        if not all([dev_name, client_hardware_id]):
            emit('save_device_response', {'status': 'error', 'message': 'Missing device info'})
            return
            
        try:
            device = _get_device_from_hardware_id(client_hardware_id)
            if device:
                device.dev_name = dev_name

                if user_id:
                    device.user_id = user_id
                db.session.add(device)
                dev_id_to_return = device.dev_id
                logger.info(f"Device updated: HW ID '{client_hardware_id}' -> DB ID {dev_id_to_return}")
            else:
                new_device = Device(user_id=user_id, dev_name=dev_name, dev_status=True, dev_hardware_id=client_hardware_id)
                db.session.add(new_device)
                db.session.flush()
                dev_id_to_return = new_device.dev_id
                logger.info(f"New device created: HW ID '{client_hardware_id}' -> DB ID {dev_id_to_return}")

            db.session.commit()
            emit('save_device_response', {'status': 'success', 'message': 'Device saved successfully', 'dev_id': dev_id_to_return})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error on save_device: {e}")
            emit('save_device_response', {'status': 'error', 'message': f'Database error: {e}'})


    @socketio.on('get_stats')
    def handle_get_stats():
        stats = perf_monitor.get_stats()
        stats['server_time'] = time.strftime('%H:%M:%S')
        emit('stats', stats)


    @socketio.on('frame')
    def handle_frame(data):
        try:
            # --- Phần 1: Lấy dữ liệu và khởi tạo ---
            parsed_data = json.loads(data) if isinstance(data, str) else data
            image_b64 = parsed_data.get('image')
            if not image_b64: return

            start_recv = time.time()
            image_data = base64.b64decode(image_b64.split(',', 1)[1])
            recv_time = time.time() - start_recv
            image_size_kb = len(image_data) / 1024
            speed_kbps = image_size_kb / recv_time if recv_time > 0 else 0
            logger.info(f"⏱️ Image size: {image_size_kb:.2f} KB, ⏬ Download speed: {speed_kbps:.2f} KB/s")

            client_hardware_id = parsed_data.get('dev_id')
            model_id = parsed_data.get('model_id')

            current_model = model_manager.get_model(model_id)
            if not current_model:
                emit('error', {'message': f'Server could not load model ID {model_id}.'})
                return
            
            device = _get_device_from_hardware_id(client_hardware_id)
            if not device: return

            # --- Phần 2: Xử lý ảnh và nhận diện (giữ nguyên) ---
            image_data = base64.b64decode(image_b64.split(',', 1)[1])
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            results = current_model(image, conf=0.25, iou=0.45, verbose=False)
            detections = []
            fire_detections = []

            for result in results:
                if result.boxes:
                    for box in result.boxes.data.tolist():
                        if len(box) >= 6:
                            x1, y1, x2, y2, score, cls = box
                            label = current_model.names.get(int(cls), 'unknown')
                            detection_data = {'bbox': [x1, y1, x2, y2], 'confidence': score, 'label': label}
                            detections.append(detection_data)
                            
                            if label.lower() == 'fire':
                                fire_detections.append(detection_data)

            # --- Phần 3: Logic lưu trữ - ĐÂY LÀ NƠI THAY ĐỔI ---
            if fire_detections:
                
                # === PHẦN MỚI: VẼ BOUNDING BOX LÊN ẢNH TRƯỚC KHI LƯU ===
                # Tạo một đối tượng có thể vẽ lên ảnh
                image_origin = Image.open(io.BytesIO(image_data)).convert('RGB')
                bbox_image = image_origin.copy()
                draw = ImageDraw.Draw(bbox_image)  # ✅ vẽ trực tiếp lên bbox_image

                try:
                    # Thử tải một font chữ cụ thể, nếu không có thì dùng font mặc định
                    font = ImageFont.truetype("arial.ttf", 15)
                except IOError:
                    font = ImageFont.load_default()

                # Lặp qua các phát hiện lửa và vẽ chúng lên ảnh
                for det in fire_detections:
                    bbox = det['bbox']
                    confidence = det['confidence']
                    
                    # Vẽ hình chữ nhật
                    draw.rectangle(bbox, outline="red", width=3)
                    
                    # Chuẩn bị và vẽ chữ (confidence score)
                    text = f"Fire: {(confidence * 100):.1f}%"
                    text_position = (bbox[0], bbox[1] - 15) # Vị trí ngay trên bounding box
                    draw.text(text_position, text, fill="red", font=font)
                # ==========================================================

                # Bây giờ, đối tượng 'image' đã có các bounding box được vẽ lên
                # Ta truyền tấm ảnh đã được chỉnh sửa này vào hàm lưu file
                # log_img_path = _save_image_and_get_path(image, device.dev_id)
                
                # Hàm lưu log vào CSDL không thay đổi
                _save_detection_log(
                    dev_id=device.dev_id,
                    model_id=model_id,
                    orig_image=image_origin,
                    bbox_image=bbox_image,
                    detections=fire_detections,  # chính xác bbox YOLO detect ra
                    cooldown_seconds=2
                )

            # --- Phần 4: Gửi kết quả và cập nhật hiệu năng (giữ nguyên) ---
            perf_monitor.update(len(detections), data_size_kb=image_size_kb, recv_time=recv_time)

            emit('detections', {'detections': detections})
            
        except Exception as e:
            logger.error(f"Error in handle_frame: {e}")
            emit('error', {'message': 'An error occurred on the server.'})