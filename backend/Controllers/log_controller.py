# backend/Controllers/log_controller.py

import os
import io
import base64
import time
import logging
import threading
from PIL import Image, ImageDraw, ImageFont
import csv

from sqlalchemy import or_, func
from flask import current_app, jsonify, request, session, has_request_context, Response
from sqlalchemy import or_
from backend.Models.devices_model import Device
from backend.Models.models_model import Model
from backend.Models.users_model import User
from backend.extensions import socketio

from backend.Models import db, Log
from backend.Models.log_bboxes_model import LogBBox
from backend.utils.models_manager import model_manager
from backend.services.log_noti_send_email import handle_post_log_events
from backend.services.fire_persistence_tracker import FirePersistenceTracker



# Lưu thời gian log gần nhất theo thiết bị để giới hạn tốc độ ghi log (0.3s)
last_log_times = {}

# Bộ đếm kiểm tra lửa kéo dài ≥ 5s và giới hạn gửi email mỗi 10p
fire_persist_tracker = FirePersistenceTracker(min_duration=5, cooldown=6000)

# ✔️ Bộ nhớ tạm chứa các log có lửa, để sau 5s chọn log tốt nhất (confidence cao nhất)
fire_log_buffer = {}  # dev_id: list[{"log_id", "confidence", "image_path"}]


# Hàm chạy nền để xử lý gửi email
def trigger_notification_in_background(app, log_id, user_email, user_name):
    with app.app_context():
        try:
            ok, msg, noti_id = handle_post_log_events(log_id, user_email, user_name)
            if ok:
                logging.info(f"Gửi thông báo thành công cho log_id: {log_id} tới {user_email}.")
            else:
                logging.warning(f"Gửi thông báo thất bại cho log_id: {log_id}. Lý do: {msg}")
        except Exception as e:
            logging.error(f"Lỗi không xác định trong tác vụ nền cho log_id: {log_id}. Lỗi: {e}", exc_info=True)


# Hàm xử lý một frame gửi từ API
def handle_detect_from_api(data):
    from backend.socket.common import perf_monitor
    dev_id = data.get("dev_id")
    try:
        # Lấy dữ liệu từ client gửi lên
        image_b64 = data.get("image")
        model_id = data.get("model_id")
        dev_id = data.get("dev_id")

        if not image_b64 or not model_id or not dev_id:
            return False, "Thiếu image / model_id / dev_id"

        # Decode ảnh từ base64
        header, encoded = image_b64.split(",", 1)
        image_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')

        # Load mô hình YOLO
        start_time = time.time()
        model = model_manager.get_model(model_id)
        if not model:
            return False, f"Không load được model ID {model_id}"
        results = model(image, conf=0.25, iou=0.45, verbose=False)
        end_time = time.time()
        perf_monitor.last_fps = 1.0 / (end_time - start_time)

        # Trích xuất kết quả phát hiện
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

        # Nếu không phát hiện lửa thì trả kết quả ngay
        if not fire_detections:
            return True, {"detections": detections, "message": "Không phát hiện cháy"}

        # Cooldown 0.3s để tránh ghi log quá nhanh
        now = time.time()
        if now - last_log_times.get(dev_id, 0) < 0.3:
            logging.info(f"!!! Bỏ QUA DO COOLDOWN 0.3 GIÂY CHO dev_id: {dev_id} !!!")
            return True, {"detections": detections, "message": "Cooldown, chưa ghi log"}

        # Ghi log ảnh
        save_dir = os.path.join('frontend', 'static', 'log_images', str(dev_id))
        os.makedirs(save_dir, exist_ok=True)
        new_log = Log(dev_id=dev_id, model_id=model_id)
        db.session.add(new_log)
        db.session.flush()
        log_id = new_log.log_id

        origin_path = os.path.join(save_dir, f"{log_id}_origin_model{model_id}_dev{dev_id}.jpg")
        bbox_path = os.path.join(save_dir, f"{log_id}_bbox_model{model_id}_dev{dev_id}.jpg")
        image_origin = image.copy()
        bbox_image = image.copy()
        draw = ImageDraw.Draw(bbox_image)

        # Vẽ bounding box
        try:
            font = ImageFont.truetype("arial.ttf", 15)
        except IOError:
            font = ImageFont.load_default()
        for det in fire_detections:
            x1, y1, x2, y2 = det['bbox']
            confidence = det['confidence']
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
            draw.text((x1, y1 - 15), f"Fire: {confidence*100:.1f}%", fill="red", font=font)

        # Lưu ảnh
        image_origin.save(origin_path)
        bbox_image.save(bbox_path)
        new_log.log_image_path = origin_path.replace("\\", "/")

        # Lưu bounding box vào DB
        for det in fire_detections:
            x1, y1, x2, y2 = det['bbox']
            width, height = x2 - x1, y2 - y1
            db.session.add(LogBBox(
                log_id=log_id,
                confidence=float(det['confidence']),
                x_center=x1 + width / 2,
                y_center=y1 + height / 2,
                width=width,
                height=height
            ))
        db.session.commit()
        last_log_times[dev_id] = now

        # ⚠️ Cập nhật bộ nhớ tạm log có lửa
        is_fire = bool(fire_detections)
        if is_fire:
            max_conf = max(det['confidence'] for det in fire_detections)
            fire_log_buffer.setdefault(dev_id, []).append({
                "log_id": log_id,
                "confidence": max_conf,
                "image_path": origin_path.replace("\\", "/")
            })
        else:
            fire_log_buffer.pop(dev_id, None)

        # Nếu đủ điều kiện gửi cảnh báo → chọn log tốt nhất và gửi
        if fire_persist_tracker.should_send_alert(dev_id, is_fire):
            logging.info(f"🔥 Thiết bị {dev_id} đủ điều kiện gửi email")
            if has_request_context() and "user_id" in session:
                user = User.query.get(session['user_id'])
                if user:
                    app_context = current_app._get_current_object()
                    user_email = user.user_email
                    user_name = user.user_name

                    # ✔️ Chọn log có độ tin cậy cao nhất trong bộ nhớ tạm
                    top_log = max(fire_log_buffer.get(dev_id, []), key=lambda x: x["confidence"], default=None)
                    fire_log_buffer.pop(dev_id, None)
                    if top_log:
                        top_log_id = top_log["log_id"]
                        logging.info(f"🔥 Chọn log_id={top_log_id} để gửi email (conf={top_log['confidence']:.2f})")
                        socketio.start_background_task(
                            target=trigger_notification_in_background,
                            app=app_context,
                            log_id=top_log_id,
                            user_email=user_email,
                            user_name=user_name
                        )
                else:
                    logging.warning(f"⚠️ Không tìm thấy user với user_id: {session['user_id']}")
            else:
                logging.warning("⚠️ Không gửi thông báo vì không có session")
        else:
            logging.debug(f"🔥 Dev {dev_id}: Lửa bị ngắt → reset timer")

        return True, {"detections": detections, "message": "Đã lưu log", "log_id": log_id}

    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi xử lý: {e}"

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
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        logging.error(f"Lỗi khi lấy dữ liệu log: {e}", exc_info=True)
        return jsonify({'draw': 0, 'recordsTotal': 0, 'recordsFiltered': 0, 'data': [], 'error': "Lỗi server"})

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




#Xuất file csv#
def export_logs_to_csv():
    try:
        user_id = session.get('user_id')
        user_roles = session.get('user_roles', [])
        if not user_id:
            return Response("Unauthorized", status=401)

        search_value = request.args.get('search', '').strip()

        if 'admin' not in user_roles and 'police' not in user_roles:
            return Response("Bạn không có quyền thực hiện hành động này.", status=403)

        bbox_subquery = db.session.query(
            LogBBox.log_id,
            func.max(LogBBox.confidence).label('max_confidence')
        ).group_by(LogBBox.log_id).subquery()

        base_query = db.session.query(
            Log.log_id,
            Device.dev_name,
            Model.model_name,
            Log.log_create_at,
            bbox_subquery.c.max_confidence  
        ).join(Device, Log.dev_id == Device.dev_id)\
         .join(Model, Log.model_id == Model.model_id)\
         .outerjoin(bbox_subquery, Log.log_id == bbox_subquery.c.log_id) 

        if 'admin' not in user_roles:
            base_query = base_query.filter(Device.user_id == user_id)

        if search_value:
            base_query = base_query.filter(or_(
                Device.dev_name.ilike(f'%{search_value}%'),
                Model.model_name.ilike(f'%{search_value}%')
            ))

        results = base_query.order_by(Log.log_create_at.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(['ID Log', 'Tên thiết bị', 'Tên mô hình', 'Ngày tạo', 'Độ tin cậy cao nhất (%)'])

        for row in results:

            confidence_percent = f"{(row.max_confidence * 100):.2f}" if row.max_confidence is not None else "N/A"
            
            writer.writerow([
                row.log_id,
                row.dev_name,
                row.model_name,
                row.log_create_at.strftime('%Y-%m-%d %H:%M:%S'),
                confidence_percent
            ])
        csv_data = output.getvalue().encode('utf-8-sig')

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=fire_logs_export.csv"}
        )
        
    except Exception as e:
        logging.error(f"Lỗi khi xuất CSV: {e}", exc_info=True)
        return Response("Lỗi server khi tạo file CSV", status=500)