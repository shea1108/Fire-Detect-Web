from flask import Blueprint, request, jsonify
from backend.Controllers.device_controller import save_device, find_devices_by_user

device_bp = Blueprint('device_bp', __name__)

@device_bp.route('/api/save_device', methods=['POST'])
def api_save_device():
    data = request.json
    save_device(data)
    return jsonify({"status": "ok"})

@device_bp.route('/api/devices/<user_id>', methods=['GET'])
def api_get_devices(user_id):
    devices = find_devices_by_user(user_id)
    return jsonify({"devices": devices})