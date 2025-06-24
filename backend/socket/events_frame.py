# backend/socket/events_frame.py
import base64
import io
import json
import logging
import time
from collections import deque
from PIL import Image
from flask import request
from flask_socketio import emit

from backend.Models.devices_model import Device

logger = logging.getLogger(__name__)

perf_monitor = None  # Sẽ được inject từ ngoài


def _get_device_from_hardware_id(hw_id):
    if not hw_id:
        return None
    return Device.query.filter_by(dev_hardware_id=hw_id).first()


def register_frame_events(socketio, _perf_monitor):
    global perf_monitor
    perf_monitor = _perf_monitor

    @socketio.on('frame')
    def handle_frame(data):
        from backend.Controllers.log_controller import handle_detect_from_api

        try:
            overall_start = time.time()  # Bắt đầu đo
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
            device = _get_device_from_hardware_id(client_hardware_id)
            if not device:
                return

            # Gọi controller xử lý
            payload = {
                "image": image_b64,
                "model_id": model_id,
                "dev_id": device.dev_id
            }
            result = handle_detect_from_api(payload)

            if isinstance(result, tuple):
                success, res_data = result
                if not success:
                    emit('error', {'message': str(res_data)})
                    return
                detections = res_data.get("detections", [])
            else:
                detections = result.get("detections", [])


            # ✅ Tính thời gian xử lý YOLO + decode + logic
            elapsed = time.time() - overall_start
            current_fps = 1.0 / elapsed if elapsed > 0 else 0


            # ✅ Cập nhật thống kê
            perf_monitor.update(len(detections), image_size_kb, recv_time)
            perf_monitor.last_fps = current_fps  # ✅ Thêm dòng này để cập nhật giá trị mới
            # perf_monitor.last_fps = current_fps  # Thêm dòng này
            emit('detections', {'detections': detections, 'fps': perf_monitor.last_fps})

        except Exception as e:
            logger.error(f"Error in handle_frame: {e}")
            emit('error', {'message': 'Server error occurred during frame processing.'})