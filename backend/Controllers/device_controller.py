from flask import jsonify
from backend.Models import db
from backend.Models.devices_model import Device


def save_device(data):
    print("Received data:", data)

    dev_name = data.get('dev_name')
    user_id = data.get('user_id')

    if not user_id or not dev_name:
        return jsonify({"status": "error", "message": "Missing device info"}), 400

    try:
        existing_device = Device.query.filter_by(dev_name=dev_name, user_id=user_id).first()

        if existing_device:
            existing_device.dev_status = True
            print(f"Device '{dev_name}' exists, updated status.")
        else:
            new_device = Device(
                user_id=user_id,
                dev_name=dev_name,
                dev_status=True
            )
            db.session.add(new_device)
            print(f"New device '{dev_name}' inserted.")

        db.session.commit()
        return jsonify({"status": "ok"})

    except Exception as e:
        db.session.rollback()
        print("Error while saving device:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    
    
def find_devices_by_user(user_id):
    try:
        devices = Device.query.filter_by(user_id=user_id).all()
        device_list = [
            {
                
                "dev_id": device.dev_id, 
                "dev_name": device.dev_name,
                "dev_status": device.dev_status
            }
            for device in devices
        ]
        return device_list
    except Exception as e:
        print("Error while fetching devices:", e)
        return []
