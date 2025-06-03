from flask_socketio import emit
from PIL import Image
import base64
import io
import numpy as np
from ultralytics import YOLO
import cv2
import logging
import time
import torch
import os
import uuid
import json
from flask import request
from backend.Models import db, Log
from backend.Models.devices_model import Device

# Configure logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load YOLO model once at startup 
try:
    model = YOLO('Yolo/best.pt')
    if torch.cuda.is_available():
        model.to('cuda')
        logger.info("YOLO model loaded successfully and moved to GPU (CUDA)")
    else:
        logger.info("YOLO model loaded successfully (running on CPU)")
except Exception as e:
    logger.error(f"Failed to load YOLO model: {e}")
    model = None

# Global performance monitor instance 
class PerformanceMonitor:
    def __init__(self):
        self.frame_count = 0
        self.detection_count = 0
        self.start_time = None
        self.last_log_time = time.time()
        self.log_interval = 5 # Log performance every 10 seconds

    def update(self, detections_count):
        if self.start_time is None:
            self.start_time = time.time()

        self.frame_count += 1
        self.detection_count += detections_count

        current_time = time.time()
        if current_time - self.last_log_time >= self.log_interval:
            self.log_stats()
            self.last_log_time = current_time

    def log_stats(self):
        stats = self.get_stats()
        if stats:
            logger.info(f"Performance Stats - Frames: {stats.get('frames_processed', 0)}, Detections: {stats.get('total_detections', 0)}, FPS: {stats.get('fps', 0):.2f}, Uptime: {stats.get('uptime_seconds', 0):.2f}s")

    def get_stats(self):
        if self.start_time is None:
            return {}

        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0

        return {
            'frames_processed': self.frame_count,
            'total_detections': self.detection_count,
            'fps': round(fps, 2),
            'uptime_seconds': round(elapsed, 2)
        }

perf_monitor = PerformanceMonitor()

# Thêm biến này để quản lý thời gian cooldown cho mỗi dev_id
last_log_times = {} 


# Hàm preprocess_image_for_fire_detection 
def preprocess_image_for_fire_detection(image):
    try:
        img_array = np.array(image)
        return Image.fromarray(img_array)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return image

# Hàm filter_fire_detections 
def filter_fire_detections(detections, min_confidence=0.5):
    filtered = []
    for det in detections:
        if 'label' in det and isinstance(det['label'], str) and \
           det['confidence'] >= min_confidence and \
           ('fire' in det['label'].lower() or 'flame' in det['label'].lower()):
            filtered.append(det)
    return filtered

# Hàm check_model_health 
def check_model_health():
    if model is None:
        return False, "YOLO model not loaded. Please check the model path and loading process."

    try:
        test_image = Image.new('RGB', (64, 64), color='red')
        results = model(test_image, verbose=False, device='cpu', imgsz=32)
        _ = list(results) 
        return True, "YOLO model is healthy and ready for inference."
    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        return False, f"Model error during health check: {e}"

# Sửa đổi hàm save_fire_log để nhận dev_id là số nguyên và thêm cooldown
def save_fire_log(dev_id, model_id, confidence, image_path, cooldown_seconds=5):
    """
    Save fire detection log to database and print log info with cooldown.
    dev_id here is expected to be an INTEGER.
    """
    # Đảm bảo dev_id là số nguyên
    if not isinstance(dev_id, int):
        logger.error(f"❌ save_fire_log: dev_id không phải số nguyên: {dev_id}. Không thể lưu log.")
        return False

    now = time.time()
    # Lấy thời gian log cuối cùng cho dev_id cụ thể
    last_time = last_log_times.get(dev_id, 0) 

    # Nếu chưa đủ thời gian cooldown, bỏ qua
    if now - last_time < cooldown_seconds:
        logger.info(f"⏳ Cooldown active for dev_id {dev_id}. Skipping log.")
        return False

    try:
        new_log = Log(
            dev_id=dev_id, 
            model_id=model_id, # model_id is now passed as an integer
            log_fire_confidence=confidence,
            log_image_path=image_path
        )
        db.session.add(new_log)
        db.session.commit()
        last_log_times[dev_id] = now # Cập nhật thời gian log cuối cùng
        logger.info(f"🔥 [FIRE DETECTED] | Confidence: {confidence:.2f} | Device DB ID: {dev_id} | Model ID: {model_id} | Image: {image_path}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error saving fire detection log to database for dev_id {dev_id}: {e}")
        return False

def register_socketio(socketio):
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected.")
        health_ok, health_msg = check_model_health()
        emit('status', {
            'message': 'Connected to fire detection server',
            'model_health': health_ok,
            'health_details': health_msg
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected.")


    @socketio.on('save_device')
    def handle_save_device(data):
        logger.info(f"Received save_device request: {data}")
        dev_name = data.get('dev_name')
        user_id = data.get('user_id')

        client_hardware_id = data.get('dev_id') 

        if not all([dev_name, user_id, client_hardware_id]):
            logger.error(f"Missing info for save_device: {data}")
            emit('save_device_response', {'status': 'error', 'message': 'Missing required device information'}, room=request.sid)
            return

        try:

            existing_device = Device.query.filter_by(dev_hardware_id=client_hardware_id).first()

            dev_id_to_return = None

            if existing_device:

                existing_device.dev_name = dev_name
                existing_device.user_id = user_id 
                existing_device.dev_status = True 
                db.session.add(existing_device)
                dev_id_to_return = existing_device.dev_id 
                logger.info(f"Existing device updated: Hardware ID '{client_hardware_id}' -> DB ID: {dev_id_to_return}")
            else:

                new_device = Device(
                    user_id=user_id,
                    dev_name=dev_name,
                    dev_status=True,
                    dev_hardware_id=client_hardware_id
                )
                db.session.add(new_device)
                db.session.flush() 
                dev_id_to_return = new_device.dev_id 
                logger.info(f"New device created: Hardware ID '{client_hardware_id}' -> DB ID: {dev_id_to_return}")

            db.session.commit()
            emit('save_device_response', {
                'status': 'success',
                'message': 'Device saved/updated successfully',
                'dev_id': dev_id_to_return
            }, room=request.sid)

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving/updating device: {e}")
            emit('save_device_response', {'status': 'error', 'message': f'Failed to save device: {e}'}, room=request.sid)


    @socketio.on('save_log')
    def handle_save_log(data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in save_log: {e}")
                emit('save_log_response', {'status': 'error', 'message': 'Invalid JSON format'}, room=request.sid)
                return

        confidence = data.get('confidence')
        base64_image = data.get('base64Image')

        client_hardware_id = data.get('dev_id') 

        model_id = 1 

        if not all([confidence, base64_image, client_hardware_id]): 
            logger.warning(f"Missing essential save_log data: confidence={confidence}, base64Image present={bool(base64_image)}, client_hardware_id={client_hardware_id}")
            emit('save_log_response', {'status': 'error', 'message': 'Missing required data'}, room=request.sid)
            return

        # --- TÌM DEV_ID SỐ NGUYÊN TỪ DEV_HARDWARE_ID CHUỖI ---
        device = Device.query.filter_by(dev_hardware_id=client_hardware_id).first()
        if not device:
            logger.error(f"❌ Device with hardware ID '{client_hardware_id}' not found. Cannot save log.")
            emit('save_log_response', {'status': 'error', 'message': f"Device with hardware ID '{client_hardware_id}' not found."}, room=request.sid)
            return

        dev_id_integer = device.dev_id 


        try:
            if ',' in base64_image:
                base64_image = base64_image.split(',')[1]
            image_data = base64.b64decode(base64_image)

            # Tạo thư mục lưu nếu chưa có, sử dụng dev_id (số nguyên) để tổ chức
            save_dir = os.path.join('static', 'log_images', str(dev_id_integer))
            os.makedirs(save_dir, exist_ok=True)

            filename = f"log_{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            logger.info(f"Saved log image for device DB ID {dev_id_integer} at {filepath}")
        except Exception as e:
            logger.error(f"Error saving log image for device DB ID {dev_id_integer}: {e}")
            emit('save_log_response', {'status': 'error', 'message': 'Failed to save image'}, room=request.sid)
            return

        # Lưu log vào DB
        try:
            # Gọi hàm save_fire_log với dev_id_integer
            log_saved_successfully = save_fire_log(dev_id_integer, model_id, float(confidence), filepath)

            if log_saved_successfully:
                emit('save_log_response', {'status': 'success', 'message': 'Log saved successfully'}, room=request.sid)
            else:
                emit('save_log_response', {'status': 'info', 'message': 'Log skipped due to cooldown'}, room=request.sid)
        except Exception as e:
            logger.error(f"Error saving log to DB for device DB ID {dev_id_integer}: {e}")
            emit('save_log_response', {'status': 'error', 'message': 'Failed to save log to database'}, room=request.sid)


    @socketio.on('get_stats')
    def handle_get_stats():
        stats = perf_monitor.get_stats()
        emit('stats', stats)

    @socketio.on('frame')
    def handle_frame(data):
        if model is None:
            emit('error', {'message': 'YOLO model is not loaded. Cannot process frames.'}, room=request.sid)
            return

        image_b64 = None
        # dev_id từ client bây giờ là dev_hardware_id (chuỗi)
        client_hardware_id = 'unknown_device_hardware_id' 
        # Set model_id to 1 directly
        model_id = 1 

        # Xử lý các định dạng input 
        if isinstance(data, str):
            data = data.strip()
            if data.startswith('data:image/jpeg;base64,') or data.startswith('data:image/png;base64,'):
                image_b64 = data
            elif data.startswith('{'):
                try:
                    parsed_data = json.loads(data)
                    image_b64 = parsed_data.get('image')
                    # Lấy dev_id (chuỗi) từ client
                    client_hardware_id = parsed_data.get('dev_id', client_hardware_id) 
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON parsing error from frame for client {request.sid}: {e}. Received: {data[:200]}...")
                    emit('error', {'message': 'Invalid JSON data for frame.'}, room=request.sid)
                    return
            else:
                logger.error(f"❌ Unknown frame data format for client {request.sid}. Expected base64 string or JSON. Received: {data[:50]}...")
                emit('error', {'message': 'Invalid frame data format.'}, room=request.sid)
                return
        elif isinstance(data, dict):
            image_b64 = data.get('image')
            # Lấy dev_id (chuỗi) từ client
            client_hardware_id = data.get('dev_id', client_hardware_id) 
          
        else:
            logger.error(f"❌ Unexpected frame data type for client {request.sid}: {type(data)}. Expected string or dict.")
            emit('error', {'message': 'Invalid data type for frame.'}, room=request.sid)
            return

        if not image_b64:
            logger.error(f"❌ No valid image data found in the 'frame' event for client {request.sid}.")
            emit('error', {'message': 'No image data provided in the frame.'}, room=request.sid)
            return

        # --- TÌM DEV_ID SỐ NGUYÊN TỪ DEV_HARDWARE_ID CHUỖI ---
        device = Device.query.filter_by(dev_hardware_id=client_hardware_id).first()
        if not device:
            logger.error(f"❌ Device with hardware ID '{client_hardware_id}' not found. Cannot process frame.")
            emit('error', {'message': f"Device with hardware ID '{client_hardware_id}' not found."}, room=request.sid)
            return

        dev_id_integer = device.dev_id # Lấy dev_id (số nguyên) từ đối tượng device đã tìm được

        # Decode base64 image 
        try:
            if ',' in image_b64:
                image_data = base64.b64decode(image_b64.split(',')[1])
            else:
                image_data = base64.b64decode(image_b64)
        except Exception as e:
            logger.error(f"Failed to decode base64 image data for client {request.sid}: {e}")
            emit('error', {'message': 'Failed to decode image data.'}, room=request.sid)
            return

        # Convert to PIL Image and apply optional preprocessing/resizing 
        try:
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            image = preprocess_image_for_fire_detection(image)
            max_size = 640
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        except Exception as e:
            logger.error(f"Failed to process image for client {request.sid}: {e}")
            emit('error', {'message': 'Failed to convert image for processing.'}, room=request.sid)
            return

        # Save image temporarily for debugging or logging if needed
        image_save_path = None
        try:
            image_id_uuid = str(uuid.uuid4())
            # Tổ chức uploads theo dev_id (số nguyên)
            save_dir = os.path.join('static', 'uploads', str(dev_id_integer))
            os.makedirs(save_dir, exist_ok=True)
            image_save_path = os.path.join(save_dir, f'{image_id_uuid}.jpg')
            image.save(image_save_path)
        except Exception as e:
            logger.warning(f"Failed to save temporary image {image_id_uuid}.jpg for device DB ID {dev_id_integer}: {e}")

        # Run YOLO detection
        detections = []
        try:
            results = model(image, conf=0.25, iou=0.45, max_det=100, verbose=False)

            for result in results:
                if result.boxes is not None:
                    for box in result.boxes.data.tolist():
                        if len(box) >= 6:
                            x1, y1, x2, y2, score, cls = box[:6]

                            if all(isinstance(coord, (int, float)) for coord in [x1, y1, x2, y2]):
                                label = model.names.get(int(cls), f'Class_{int(cls)}')
                                detection = {
                                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                    'confidence': float(score),
                                    'class_id': int(cls),
                                    'label': label
                                }
                                detections.append(detection)

                                # If 'fire' is detected, save a log entry
                                if label.lower() == 'fire':
                                    current_image_for_log = image_save_path if image_save_path else "base64_data_not_saved.jpg"
                                    try:
                                        # Pass dev_id  và model_id 
                                        save_fire_log(dev_id_integer, model_id, float(score), current_image_for_log)
                                    except Exception as e:
                                        logger.error(f"Failed to save fire log for device DB ID {dev_id_integer}: {e}")

            perf_monitor.update(len(detections))

            if detections:
                logger.info(f"Detected {len(detections)} objects in current frame from device DB ID {dev_id_integer}.")
                for det in detections:
                    logger.info(f"   - {det['label']}: {det['confidence']:.2f} (bbox: {det['bbox']})")

            emit('detections', {
                'detections': detections,
                'total_count': len(detections),
                'timestamp': int(time.time()),
                'processing_stats': {
                    'image_size': image.size,
                    'detections_found': len(detections)
                }
            }, room=request.sid)

        except Exception as e:
            logger.error(f"YOLO detection or result processing failed for client {request.sid}: {e}")
            emit('error', {'message': 'Detection failed or an error occurred during result processing.'}, room=request.sid)