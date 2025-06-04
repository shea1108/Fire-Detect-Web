

from flask import Blueprint, request, jsonify
from PIL import Image
import io
import base64


from backend.manager import model_manager

# Tạo blueprint với tiền tố URL để có tổ chức tốt hơn
bp = Blueprint('predict', __name__, url_prefix='/api/predict')




@bp.route('/file', methods=['POST'])
def predict_from_file():
    """
    Endpoint để nhận diện từ một file ảnh được tải lên.
    Có thể nhận 'model_id' từ form data để chọn model.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Lấy model_id từ request, nếu không có thì mặc định là 1
    model_id_to_use = request.form.get('model_id', 1)

    # --- BƯỚC 3: SỬ DỤNG MODEL MANAGER ĐỂ LẤY ĐÚNG MODEL ---
    current_model = model_manager.get_model(model_id_to_use)

    if not current_model:
        return jsonify({'error': f'Model ID {model_id_to_use} is not available or could not be loaded'}), 500

    try:
        image = Image.open(file.stream).convert('RGB')
        
        # --- BƯỚC 4: CHẠY DỰ ĐOÁN VỚI MODEL ĐÃ ĐƯỢC CHỌN ---
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
        return jsonify({'model_used': model_id_to_use, 'detections': detections})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/frame', methods=['POST'])
def predict_from_frame():
    """
    Endpoint để nhận diện từ một chuỗi ảnh base64 (ví dụ: từ webcam).
    Có thể nhận 'model_id' từ JSON payload để chọn model.
    """
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image data provided in JSON body'}), 400

    # Lấy model_id từ JSON, nếu không có thì mặc định là 1
    model_id_to_use = data.get('model_id', 1)

    # --- BƯỚC 3: SỬ DỤNG MODEL MANAGER ĐỂ LẤY ĐÚNG MODEL ---
    current_model = model_manager.get_model(model_id_to_use)

    if not current_model:
        return jsonify({'error': f'Model ID {model_id_to_use} is not available or could not be loaded'}), 500

    try:
        image_data = data['image'].split(',', 1)[1]
        img_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        
        # --- BƯỚC 4: CHẠY DỰ ĐOÁN VỚI MODEL ĐÃ ĐƯỢC CHỌN ---
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
        return jsonify({'model_used': model_id_to_use, 'detections': detections})
    except Exception as e:
        return jsonify({'error': str(e)}), 500