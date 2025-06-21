import os
import io
import base64
import time
import logging
from PIL import Image, ImageDraw, ImageFont

from flask import current_app, session, has_request_context, jsonify, request
from backend.Models.users_model import User
from backend.extensions import socketio

from backend.Models import db, Log, Model
from backend.Models.log_bboxes_model import LogBBox
from backend.utils.models_manager import model_manager
from backend.services.log_noti_send_email import handle_post_log_events
from backend.services.fire_persistence_tracker import FirePersistenceTracker

from sqlalchemy import or_
from backend.Models.devices_model import Device

last_log_times = {}
fire_persist_tracker = FirePersistenceTracker(min_duration=5, cooldown=6000)
fire_log_buffer = {}

# === SỬA LỖI BƯỚC 1: Thêm origin_path và bbox_path vào chữ ký hàm ===
def trigger_notification_in_background(app, log_id, user_email, user_name, origin_path, bbox_path):
    with app.app_context():
        try:
            # === SỬA LỖI BƯỚC 2: Truyền đường dẫn ảnh vào hàm xử lý ===
            ok, msg, noti_id = handle_post_log_events(
                log_id, user_email, user_name, 
                origin_path=origin_path, 
                bbox_path=bbox_path
            )
            if ok:
                logging.info(f"Gửi thông báo thành công cho log_id: {log_id} tới {user_email}.")
            else:
                logging.warning(f"Gửi thông báo thất bại cho log_id: {log_id}. Lý do: {msg}")
        except Exception as e:
            logging.error(f"Lỗi không xác định trong tác vụ nền cho log_id: {log_id}. Lỗi: {e}", exc_info=True)


def handle_detect_from_api(data):
    from backend.socket.common import perf_monitor
    dev_id = data.get("dev_id")
    try:
        image_b64 = data.get("image")
        model_id = data.get("model_id")

        if not image_b64 or not model_id or not dev_id:
            return False, "Thiếu image / model_id / dev_id"

        header, encoded = image_b64.split(",", 1)
        image_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')

        start_time = time.time()
        model = model_manager.get_model(model_id)
        if not model:
            return False, f"Không load được model ID {model_id}"
        results = model(image, conf=0.25, iou=0.45, verbose=False)
        end_time = time.time()
        if perf_monitor:
            perf_monitor.last_fps = 1.0 / (end_time - start_time) if (end_time > start_time) else 0

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

        now = time.time()
        if now - last_log_times.get(dev_id, 0) < 0.3:
            return True, {"detections": detections, "message": "Cooldown, chưa ghi log"}

        new_log = Log(dev_id=dev_id, model_id=model_id)
        db.session.add(new_log)
        db.session.flush()
        log_id = new_log.log_id

        file_name = f"{log_id}_origin_model{model_id}_dev{dev_id}.jpg"
        save_dir_physical = os.path.join('static', 'log_images', str(dev_id))
        os.makedirs(save_dir_physical, exist_ok=True)
        origin_path = os.path.join(save_dir_physical, file_name)

        bbox_file_name = file_name.replace("_origin_", "_bbox_")
        bbox_path = os.path.join(save_dir_physical, bbox_file_name)

        bbox_image = image.copy()
        draw = ImageDraw.Draw(bbox_image)
        try:
            font = ImageFont.truetype("arial.ttf", 15)
        except IOError:
            font = ImageFont.load_default()
        for det in fire_detections:
            x1, y1, x2, y2 = det['bbox']
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)

        image.save(origin_path) # Lưu ảnh gốc
        bbox_image.save(bbox_path) # Lưu ảnh có bounding box
        
        db_image_path = os.path.join('log_images', str(dev_id), file_name).replace("\\", "/")
        new_log.log_image_path = db_image_path

        for det in fire_detections:
            x1, y1, x2, y2 = det['bbox']
            width, height = x2 - x1, y2 - y1
            db.session.add(LogBBox(log_id=log_id, confidence=float(det['confidence']), x_center=x1 + width / 2, y_center=y1 + height / 2, width=width, height=height))
        db.session.commit()
        last_log_times[dev_id] = now

        is_fire = bool(fire_detections)
        if is_fire:
            max_conf = max(d['confidence'] for d in fire_detections)
            fire_log_buffer.setdefault(dev_id, []).append({
                "log_id": log_id,
                "confidence": max_conf,
                "origin_path": origin_path.replace("\\", "/"),
                "bbox_path": bbox_path.replace("\\", "/")
            })
        else:
            fire_log_buffer.pop(dev_id, None)

        if fire_persist_tracker.should_send_alert(dev_id, is_fire):
            logging.info(f"🔥 Thiết bị {dev_id} đủ điều kiện gửi email")
            if has_request_context() and "user_id" in session:
                user = User.query.get(session['user_id'])
                if user:
                    app_context = current_app._get_current_object()
                    top_log = max(fire_log_buffer.get(dev_id, []), key=lambda x: x["confidence"], default=None)
                    fire_log_buffer.pop(dev_id, None)
                    if top_log:
                        logging.info(f"🔥 Chọn log_id={top_log['log_id']} để gửi email (conf={top_log['confidence']:.2f})")
                        
                        # === SỬA LỖI BƯỚC 3: Thêm origin_path và bbox_path vào các tham số của tác vụ nền ===
                        socketio.start_background_task(
                            target=trigger_notification_in_background,
                            app=app_context,
                            log_id=top_log["log_id"],
                            user_email=user.user_email,
                            user_name=user.user_name,
                            origin_path=top_log["origin_path"], # Thêm vào
                            bbox_path=top_log["bbox_path"]      # Thêm vào
                        )

        return True, {"detections": detections, "message": "Đã lưu log", "log_id": log_id}
    except Exception as e:
        db.session.rollback()
        logging.error(f"Lỗi nghiêm trọng trong handle_detect_from_api: {e}", exc_info=True)
        return False, f"Lỗi xử lý: {str(e)}"


# ==================== CÁC HÀM KHÁC ====================

def get_all_logs_for_datatable():
    try:
        user_id = session.get('user_id')
        user_roles = session.get('user_roles', [])
        if not user_id:
            return jsonify({'draw': int(request.form.get('draw', 0)), 'recordsTotal': 0, 'recordsFiltered': 0, 'data': []})

        params = request.form
        draw = int(params.get('draw', 0))
        start = int(params.get('start', 0))
        length = int(params.get('length', 10))
        search_value = params.get('search[value]', '').strip()
        order_column_index = int(params.get('order[0][column]', 0))
        order_dir = params.get('order[0][dir]', 'asc')

        base_query = db.session.query(
            Log.log_id, Device.dev_name, Model.model_name,
            Log.log_image_path, Log.log_create_at
        ).join(Device, Log.dev_id == Device.dev_id).join(Model, Log.model_id == Model.model_id)

        if 'admin' not in user_roles:
            base_query = base_query.filter(Device.user_id == user_id)

        total_records = base_query.count()
        query = base_query
        if search_value:
            query = query.filter(or_(
                Device.dev_name.ilike(f'%{search_value}%'),
                Model.model_name.ilike(f'%{search_value}%')
            ))
        filtered_records = query.count()

        columns = [Log.log_id, Device.dev_name, Model.model_name, None, Log.log_create_at]
        order_column = columns[order_column_index]
        if order_column is not None:
            query = query.order_by(order_column.desc() if order_dir == 'desc' else order_column.asc())

        results = query.offset(start).limit(length).all()
        data = [{
            'id': row.log_id,
            'device_name': row.dev_name,
            'model_name': row.model_name,
            'image_path': '/static/' + row.log_image_path if row.log_image_path else None,
            'created_at': row.log_create_at.strftime('%Y-%m-%d %H:%M:%S')
        } for row in results]

        return jsonify({
            'draw': draw, 'recordsTotal': total_records,
            'recordsFiltered': filtered_records, 'data': data
        })

    except Exception as e:
        logging.error(f"Lỗi khi lấy dữ liệu cho DataTables: {e}", exc_info=True)
        return jsonify({'draw': int(request.form.get('draw', 0)), 'recordsTotal': 0, 'recordsFiltered': 0, 'data': [], 'error': "Lỗi server"})


def get_log_details(log_id):
    try:
        log_details = db.session.query(
            Log.log_id, Device.dev_name, Device.dev_location,
            Model.model_name, Log.log_image_path, Log.log_create_at
        ).join(Device, Log.dev_id == Device.dev_id, isouter=True).join(
            Model, Log.model_id == Model.model_id
        ).filter(Log.log_id == log_id).first()

        if not log_details:
            return jsonify({"success": False, "message": "Không tìm thấy log"}), 404

        bboxes = LogBBox.query.filter_by(log_id=log_id).all()
        bboxes_data = [{
            'confidence': bbox.confidence,
            'x_center': bbox.x_center,
            'y_center': bbox.y_center,
            'width': bbox.width,
            'height': bbox.height,
        } for bbox in bboxes]

        data = {
            'id': log_details.log_id,
            'device_name': log_details.dev_name,
            'device_location': log_details.dev_location,
            'model_name': log_details.model_name,
            'image_path': '/static/' + log_details.log_image_path if log_details.log_image_path else None,
            'created_at': log_details.log_create_at,
            'bboxes': bboxes_data
        }

        return jsonify({"success": True, "data": data})

    except Exception as e:
        logging.error(f"Lỗi khi lấy chi tiết log_id={log_id}: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Lỗi server"}), 500
