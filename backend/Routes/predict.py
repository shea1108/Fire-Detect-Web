from flask import Blueprint, request, jsonify
from PIL import Image
import io
import base64


from backend.manager import model_manager

# Tạo blueprint với tiền tố URL để có tổ chức tốt hơn
bp = Blueprint('predict', __name__, url_prefix='/api/predict')

@bp.route('/detect_image', methods=['POST'])
def detect_image_with_model():
    """
    Dự đoán từ file ảnh và model do người dùng chọn.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Không có tệp ảnh trong yêu cầu'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Chưa chọn tệp ảnh'}), 400

    model_id = request.form.get('model_id')
    if not model_id:
        return jsonify({'error': 'Thiếu model_id'}), 400

    current_model = model_manager.get_model(model_id)
    if not current_model:
        return jsonify({'error': f'Model ID {model_id} không hợp lệ'}), 400

    try:
        image = Image.open(file.stream).convert('RGB')
        results = current_model(image, conf=0.25, iou=0.45, verbose=False)

        detections = []
        for result in results:
            for box in result.boxes.data.tolist():
                if len(box) >= 6:
                    x1, y1, x2, y2, score, cls = box
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': float(score),
                        'class_id': int(cls),
                        'label': current_model.names.get(int(cls), 'unknown')
                    })

        return jsonify({'model_used': model_id, 'detections': detections})
    except Exception as e:
        return jsonify({'error': f'Lỗi xử lý ảnh: {str(e)}'}), 500

@bp.route('/detect_video_frame', methods=['POST'])
def detect_video_frame():
    """
    Dự đoán từ 1 khung hình base64 gửi lên từ video.
    Có thể nhận model_id để chọn mô hình động.
    """
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400

    model_id = data.get('model_id', 1)
    current_model = model_manager.get_model(model_id)

    if not current_model:
        return jsonify({'error': f'Model ID {model_id} không hợp lệ'}), 400

    try:
        image_data = data['image'].split(',')[1]
        img_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        
        results = current_model(image, conf=0.25, iou=0.45, verbose=False)

        detections = []
        for result in results:
            for box in result.boxes.data.tolist():
                if len(box) >= 6:
                    x1, y1, x2, y2, score, cls = box
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': float(score),
                        'class_id': int(cls),
                        'label': current_model.names.get(int(cls), 'unknown')
                    })

        return jsonify({'model_used': model_id, 'detections': detections})

    except Exception as e:
        return jsonify({'error': f'Lỗi xử lý frame: {str(e)}'}), 500
