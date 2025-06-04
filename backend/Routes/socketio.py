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
from flask import request
from flask_socketio import emit
from PIL import Image
from ultralytics import YOLO
from backend.manager import model_manager


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

def save_fire_log(dev_id, model_id, confidence, image_path, cooldown_seconds=5):
    if not isinstance(dev_id, int): return False
    now = time.time()
    if now - last_log_times.get(dev_id, 0) < cooldown_seconds: return False
    try:
        new_log = Log(dev_id=dev_id, model_id=model_id, log_fire_confidence=confidence, log_image_path=image_path)
        db.session.add(new_log)
        db.session.commit()
        last_log_times[dev_id] = now
        logger.info(f"🔥 FIRE LOGGED | Device: {dev_id} | Model: {model_id} | Confidence: {confidence:.2f}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error saving fire log: {e}")
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
        # Sửa lại key để khớp với frontend
        client_hardware_id = data.get('dev_hardware_id') 

        if not all([dev_name, user_id, client_hardware_id]):
            logger.error(f"Error: Missing device info in payload: {data}")
            emit('save_device_response', {'status': 'error', 'message': 'Missing device info'}, room=request.sid)
            return
            
        try:
            device = Device.query.filter_by(dev_hardware_id=client_hardware_id).first()
            if device:
                # Nếu thiết bị đã tồn tại, cập nhật tên
                device.dev_name = dev_name
                db.session.add(device)
                dev_id_to_return = device.dev_id
                logger.info(f"Device updated: HW ID '{client_hardware_id}' -> DB ID {dev_id_to_return}")
            else:
                # Nếu chưa có, tạo mới
                new_device = Device(user_id=user_id, dev_name=dev_name, dev_status=True, dev_hardware_id=client_hardware_id)
                db.session.add(new_device)
                db.session.flush() # Lấy id trước khi commit
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
        # --- LOGIC ĐƯỢC PHỤC HỒI ---
        try:
            parsed_data = json.loads(data) if isinstance(data, str) else data
            confidence = parsed_data.get('confidence')
            base64_image = parsed_data.get('base64Image')
            client_hardware_id = parsed_data.get('dev_id')
            model_id = int(parsed_data.get('model_id', 1))

            if not all([confidence, base64_image, client_hardware_id]):
                emit('save_log_response', {'status': 'error', 'message': 'Missing data'}, room=request.sid)
                return

            device = Device.query.filter_by(dev_hardware_id=client_hardware_id).first()
            if not device:
                emit('save_log_response', {'status': 'error', 'message': f"Device not found"}, room=request.sid)
                return
            
            image_data = base64.b64decode(base64_image.split(',', 1)[1])
            save_dir = os.path.join('static', 'log_images', str(device.dev_id))
            os.makedirs(save_dir, exist_ok=True)
            filename = f"log_{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
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
            parsed_data = json.loads(data) if isinstance(data, str) else data
            image_b64 = parsed_data.get('image')
            client_hardware_id = parsed_data.get('dev_id', 'unknown_device')
            model_id = int(parsed_data.get('model_id', 1))
            if not image_b64: return

            current_model = model_manager.get_model(model_id)
            if not current_model:
                emit('error', {'message': f'Server could not load model ID {model_id}.'}, room=request.sid)
                return
                
            device = Device.query.filter_by(dev_hardware_id=client_hardware_id).first()
            if not device: return

            image_data = base64.b64decode(image_b64.split(',', 1)[1])
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            results = current_model(image, conf=0.25, iou=0.45, verbose=False)
            detections = []
            
            for result in results:
                if result.boxes:
                    for box in result.boxes.data.tolist():
                        if len(box) >= 6:
                            x1, y1, x2, y2, score, cls = box
                            label = current_model.names.get(int(cls), 'unknown')
                            detections.append({'bbox': [x1, y1, x2, y2], 'confidence': score, 'label': label})
                            
                            # --- TÍCH HỢP LẠI VIỆC LƯU LOG KHI PHÁT HIỆN CHÁY ---
                            if label.lower() == 'fire':
                                # Lưu ảnh tạm thời để lấy đường dẫn
                                save_dir = os.path.join('static', 'log_images', str(device.dev_id))
                                os.makedirs(save_dir, exist_ok=True)
                                log_img_path = os.path.join(save_dir, f"capture_{uuid.uuid4().hex}.jpg")
                                image.save(log_img_path)
                                # Gọi hàm lưu log
                                save_fire_log(device.dev_id, model_id, float(score), log_img_path)

            perf_monitor.update(len(detections))
            emit('detections', {'detections': detections}, room=request.sid)
        except Exception as e:
            logger.error(f"Error in handle_frame: {e}")
            emit('error', {'message': 'An error occurred on the server.'}, room=request.sid)