from flask import Blueprint, request, jsonify
from PIL import Image
import io, base64
from ultralytics import YOLO

bp = Blueprint('predict', __name__)
model = YOLO('Yolo/best.pt')

@bp.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        image = Image.open(file.stream).convert('RGB')
        results = model(image)
        detections = []
        for result in results:
            for box in result.boxes.data.tolist():
                x1, y1, x2, y2, score, cls = box
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': float(score),
                    'class_id': int(cls),
                    'label': model.names[int(cls)]
                })
        return jsonify({'detections': detections})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/detect-frame', methods=['POST'])
def detect_frame():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400

    try:
        image_data = data['image'].split(',')[1]
        img_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        results = model(image)
        detections = []
        for result in results:
            for box in result.boxes.data.tolist():
                x1, y1, x2, y2, score, cls = box
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': float(score),
                    'class_id': int(cls),
                    'label': model.names[int(cls)]
                })
        return jsonify({'detections': detections})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
