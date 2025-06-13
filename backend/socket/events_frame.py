# backend/socket/events_frame.py
import base64
import io
import json
import logging
import time
from collections import deque
from PIL import Image, ImageDraw, ImageFont
from flask import request
from flask_socketio import emit

from backend.utils.models_manager import model_manager
from backend.Models import db, Log
from backend.Models.devices_model import Device
from backend.Models.models_model import Model as ModelDB
from backend.Models.log_bboxes_model import LogBBox

logger = logging.getLogger(__name__)

perf_monitor = None  # Sẽ được inject từ ngoài
last_log_times = {}


def _get_device_from_hardware_id(hw_id):
    if not hw_id:
        return None
    return Device.query.filter_by(dev_hardware_id=hw_id).first()

def _save_detection_log(dev_id, model_id, orig_image, bbox_image, detections, cooldown_seconds=3):
    if not detections or not isinstance(dev_id, int):
        return False
    now = time.time()
    if now - last_log_times.get(dev_id, 0) < cooldown_seconds:
        return False

    try:
        new_log = Log(dev_id=dev_id, model_id=model_id)
        db.session.add(new_log)
        db.session.flush()
        log_id = new_log.log_id

        import os
        save_dir = os.path.join('static', 'log_images', str(dev_id))
        os.makedirs(save_dir, exist_ok=True)

        origin_path = os.path.join(save_dir, f"{log_id}_origin_model{model_id}_dev{dev_id}.jpg")
        bbox_path = os.path.join(save_dir, f"{log_id}_bbox_model{model_id}_dev{dev_id}.jpg")
        orig_image.save(origin_path)
        bbox_image.save(bbox_path)
        new_log.log_image_path = origin_path.replace("\\", "/")

        for det in detections:
            bbox = det.get('bbox')
            confidence = det.get('confidence')
            if not bbox or confidence is None:
                continue
            x1, y1, x2, y2 = bbox
            width, height = x2 - x1, y2 - y1
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
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving log: {e}")
        return False

def register_frame_events(socketio, _perf_monitor):
    global perf_monitor
    perf_monitor = _perf_monitor

    @socketio.on('frame')
    def handle_frame(data):
        try:
            parsed_data = json.loads(data) if isinstance(data, str) else data
            image_b64 = parsed_data.get('image')
            if not image_b64:
                return

            start_recv = time.time()
            image_data = base64.b64decode(image_b64.split(',', 1)[1])
            recv_time = time.time() - start_recv
            image_size_kb = len(image_data) / 1024

            client_hardware_id = parsed_data.get('dev_id')
            model_id = parsed_data.get('model_id')
            current_model = model_manager.get_model(model_id)
            if not current_model:
                emit('error', {'message': f'Could not load model ID {model_id}.'})
                return

            device = _get_device_from_hardware_id(client_hardware_id)
            if not device:
                return

            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            results = current_model(image, conf=0.25, iou=0.45, verbose=False)
            detections, fire_detections = [], []

            for result in results:
                for box in result.boxes.data.tolist():
                    if len(box) >= 6:
                        x1, y1, x2, y2, score, cls = box
                        label = current_model.names.get(int(cls), 'unknown')
                        det = {'bbox': [x1, y1, x2, y2], 'confidence': score, 'label': label}
                        detections.append(det)
                        if label.lower() == 'fire':
                            fire_detections.append(det)

            if fire_detections:
                image_origin = Image.open(io.BytesIO(image_data)).convert('RGB')
                bbox_image = image_origin.copy()
                draw = ImageDraw.Draw(bbox_image)
                try:
                    font = ImageFont.truetype("arial.ttf", 15)
                except IOError:
                    font = ImageFont.load_default()
                for det in fire_detections:
                    bbox, confidence = det['bbox'], det['confidence']
                    draw.rectangle(bbox, outline="red", width=3)
                    draw.text((bbox[0], bbox[1]-15), f"Fire: {confidence*100:.1f}%", fill="red", font=font)

                _save_detection_log(device.dev_id, model_id, image_origin, bbox_image, fire_detections)

            perf_monitor.update(len(detections), image_size_kb, recv_time)
            emit('detections', {'detections': detections})

        except Exception as e:
            logger.error(f"Error in handle_frame: {e}")
            emit('error', {'message': 'Server error occurred during frame processing.'})
