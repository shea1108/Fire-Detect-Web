from flask_socketio import emit
from PIL import Image
import base64, io
from ultralytics import YOLO

model = YOLO('Yolo/29.5_v4_caitien.pt')

def register_socketio(socketio):
    @socketio.on('frame')
    def handle_frame(data):
        image_data = base64.b64decode(data.split(',')[1])
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
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
        emit('detections', {'detections': detections})