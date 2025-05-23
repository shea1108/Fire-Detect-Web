from ultralytics import YOLO
from flask import Flask, request, jsonify, render_template
from PIL import Image
import base64
import io

app = Flask(__name__)
model = YOLO('model/23.5_yolov8m_caithien_v2.pt')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/camera')
def camera():
    return render_template('detectcamera.html')

@app.route('/picture')
def picture():
    return render_template('detectpicture.html')

@app.route('/video')
def video():
    return render_template('detectvideo.html')

@app.route('/predict', methods=['POST'])
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

@app.route('/detect-frame', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True)
