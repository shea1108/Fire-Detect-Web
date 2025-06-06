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
from backend.Models.logbboxs_model import  db, LogBbox


from flask import request
from flask_socketio import emit
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

from backend.manager import model_manager # Giả sử bạn import từ đây


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
            if torch.cuda.is_available():
                model.to('cuda')
            
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

    def update(self, detections_count):
        if self.start_time is None: self.start_time = time.time()
        self.frame_count += 1
        self.detection_count += detections_count
        current_time = time.time()
        if current_time - self.last_log_time >= self.log_interval:
            self.log_stats()
            self.last_log_time = current_time

    def log_stats(self):
        stats = self.get_stats()
        if stats:
            logger.info(f"Performance - Frames: {stats.get('frames_processed', 0)}, Detections: {stats.get('total_detections', 0)}, FPS: {stats.get('fps', 0):.2f}")

    def get_stats(self):
        if self.start_time is None: return {}
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        return {'frames_processed': self.frame_count, 'total_detections': self.detection_count, 'fps': round(fps, 2)}

perf_monitor = PerformanceMonitor()
last_log_times = {}

# --- CÁC HÀM TIỆN ÍCH MỚI ĐỂ TRÁNH LẶP CODE ---
def _get_device_from_hardware_id(hw_id):
    """Lấy thông tin thiết bị từ DB bằng hardware ID của nó."""
    if not hw_id:
        return None
    return Device.query.filter_by(dev_hardware_id=hw_id).first()

def _save_image_and_get_path(image_data_or_pil, dev_id):
    """Lưu ảnh (bytes hoặc PIL Image) và trả về đường dẫn tệp."""
    save_dir = os.path.join('static', 'log_images', str(dev_id))
    os.makedirs(save_dir, exist_ok=True)
    filename = f"capture_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(save_dir, filename)

    if isinstance(image_data_or_pil, Image.Image):
        image_data_or_pil.save(filepath)
    else: # Giả sử là bytes
        with open(filepath, 'wb') as f:
            f.write(image_data_or_pil)
    return filepath

def _save_detection_log(dev_id, model_id, image_path, detections, cooldown_seconds=5):
    """
    Lưu một bản ghi Log và nhiều bản ghi LogBbox tương ứng.
    'detections' là một list các tuple/dict chứa bbox và confidence.
    """
    if not isinstance(dev_id, int): return False
    now = time.time()
    if now - last_log_times.get(dev_id, 0) < cooldown_seconds:
        logger.info(f"Log skipped for device {dev_id} due to cooldown.")
        return False

    try:
        # 1. Tạo bản ghi Log chính (không có confidence)
        new_log = Log(
            dev_id=dev_id,
            model_id=model_id,
            log_image_path=image_path
        )
        db.session.add(new_log)
        # Flush để lấy log_id cho các bbox sắp tới
        db.session.flush()

        # 2. Lặp qua các phát hiện và tạo các bản ghi LogBbox
        for detection in detections:
            # Giả sử detection là dict {'bbox': [x1,y1,x2,y2], 'confidence': score}
            bbox = detection.get('bbox')
            confidence = detection.get('confidence')
            
            if not bbox or confidence is None: continue

            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1
            
            new_bbox = LogBbox(
                log_id=new_log.log_id, # Sử dụng ID từ log vừa tạo
                confidence=float(confidence),
                x_center=x1 + width / 2.0,
                y_center=y1 + height / 2.0,
                width=width,
                height=height
            )
            db.session.add(new_bbox)
        
        db.session.commit()
        last_log_times[dev_id] = now
        logger.info(f"🔥 FIRE LOGGED | Device: {dev_id} | Saved {len(detections)} bboxes.")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error saving detection log: {e}")
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
        logger.info(f"Client [{request.sid}] requested models list.")
        try:
            all_models = ModelDB.query.all()
            models_list = [{'model_id': m.model_id, 'model_name': m.model_name} for m in all_models]
            emit('models_list', {'status': 'success', 'models': models_list}, room=request.sid)
        except Exception as e:
            logger.error(f"❌ Failed to get models from database: {e}")
            emit('models_list', {'status': 'error', 'message': str(e)}, room=request.sid)

    @socketio.on('save_device')
    def handle_save_device(data):
        dev_name = data.get('dev_name')
        user_id = data.get('user_id')
        client_hardware_id = data.get('dev_hardware_id') 

        if not all([dev_name, user_id, client_hardware_id]):
            logger.error(f"Error: Missing device info in payload: {data}")
            emit('save_device_response', {'status': 'error', 'message': 'Missing device info'}, room=request.sid)
            return
            
        try:
            # SỬ DỤNG HÀM TIỆN ÍCH
            device = _get_device_from_hardware_id(client_hardware_id)
            if device:
                device.dev_name = dev_name
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
            emit('save_device_response', {'status': 'success', 'message': 'Device saved successfully', 'dev_id': dev_id_to_return}, room=request.sid)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error on save_device: {e}")
            emit('save_device_response', {'status': 'error', 'message': f'Database error: {e}'}, room=request.sid)

    @socketio.on('save_log')
    def handle_save_log(data):
        # LƯU Ý: Handler này được giữ lại để tương thích ngược. Logic chính để lưu log
        # giờ đây nằm trong 'handle_frame' để backend chủ động quyết định việc lưu.
        try:
            parsed_data = json.loads(data) if isinstance(data, str) else data
            confidence = parsed_data.get('confidence')
            base64_image = parsed_data.get('base64Image')
            client_hardware_id = parsed_data.get('dev_id')
            model_id = int(parsed_data.get('model_id', 1))

            if not all([confidence, base64_image, client_hardware_id]):
                emit('save_log_response', {'status': 'error', 'message': 'Missing data'}, room=request.sid)
                return

            device = _get_device_from_hardware_id(client_hardware_id)
            if not device:
                emit('save_log_response', {'status': 'error', 'message': f"Device not found"}, room=request.sid)
                return
            
            image_data = base64.b64decode(base64_image.split(',', 1)[1])
            # SỬ DỤNG HÀM TIỆN ÍCH
            filepath = _save_image_and_get_path(image_data, device.dev_id)
            
            if save_fire_log(device.dev_id, model_id, float(confidence), filepath):
                emit('save_log_response', {'status': 'success', 'message': 'Log saved'}, room=request.sid)
            else:
                emit('save_log_response', {'status': 'info', 'message': 'Log skipped (cooldown)'}, room=request.sid)
        except Exception as e:
            emit('save_log_response', {'status': 'error', 'message': str(e)}, room=request.sid)
    
    @socketio.on('get_stats')
    def handle_get_stats():
        emit('stats', perf_monitor.get_stats())

    @socketio.on('frame')
    def handle_frame(data):
        try:
            # --- Phần 1: Lấy dữ liệu và khởi tạo (giữ nguyên) ---
            parsed_data = json.loads(data) if isinstance(data, str) else data
            image_b64 = parsed_data.get('image')
            if not image_b64: return
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
                draw = ImageDraw.Draw(image)
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
                log_img_path = _save_image_and_get_path(image, device.dev_id)
                
                # Hàm lưu log vào CSDL không thay đổi
                _save_detection_log(device.dev_id, int(model_id), log_img_path, fire_detections)

            # --- Phần 4: Gửi kết quả và cập nhật hiệu năng (giữ nguyên) ---
            perf_monitor.update(len(detections))
            emit('detections', {'detections': detections})
            
        except Exception as e:
            logger.error(f"Error in handle_frame: {e}")
            emit('error', {'message': 'An error occurred on the server.'})