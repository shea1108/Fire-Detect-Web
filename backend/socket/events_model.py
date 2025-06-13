# backend/socket/events_model.py

from flask import session
from flask_socketio import emit
from backend.Models.models_model import Model as ModelDB
import logging

logger = logging.getLogger(__name__)

def register_model_events(socketio):
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
                    models = [first_model]

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
        from backend.Models.devices_model import Device
        from backend.Models import db

        user_id = session.get('user_id') 
        dev_name = data.get('dev_name')
        client_hardware_id = data.get('dev_hardware_id') 

        if user_id is None:
            logger.warning(f"Guest user is saving device: HW ID '{client_hardware_id}'")

        if not all([dev_name, client_hardware_id]):
            emit('save_device_response', {'status': 'error', 'message': 'Missing device info'})
            return

        try:
            device = Device.query.filter_by(dev_hardware_id=client_hardware_id).first()
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
