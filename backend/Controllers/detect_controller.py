import base64
import io
from PIL import Image
from backend.utils.models_manager import model_manager
import logging

def handle_detect_preview(data):
    try:
        image_b64 = data.get("image")
        model_id = data.get("model_id")

        if not image_b64 or not model_id:
            return False, "Thiếu image / model_id"

        header, encoded = image_b64.split(",", 1)
        image_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')

        model = model_manager.get_model(model_id)
        if not model:
            return False, f"Không load được model ID {model_id}"

        results = model(image, conf=0.25, iou=0.45, verbose=False)

        detections = []
        for result in results:
            for box in result.boxes.data.tolist():
                if len(box) >= 6:
                    x1, y1, x2, y2, score, cls = box
                    label = model.names.get(int(cls), 'unknown')
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': float(score),
                        'label': label,
                        'class_id': int(cls)
                    })

        return True, {"detections": detections}

    except Exception as e:
        logging.exception("Lỗi trong handle_detect_preview")
        return False, f"Lỗi xử lý ảnh: {str(e)}"
