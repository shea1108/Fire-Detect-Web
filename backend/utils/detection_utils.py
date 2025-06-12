import os
from PIL import Image
from backend.manager import model_manager

def detect_fire(image_path, model_id=1):
    """
    Hàm phát hiện lửa từ ảnh đầu vào và model_id cụ thể.
    Trả về danh sách các tuple (bbox, confidence) nếu phát hiện ra lửa.
    """
    try:
        image = Image.open(image_path).convert("RGB")
        model = model_manager.get_model(model_id)
        if not model:
            print(f"❌ detect_fire: Không load được model_id {model_id}")
            return []

        results = model(image, conf=0.25, iou=0.45, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes.data.tolist():
                if len(box) >= 6:
                    x1, y1, x2, y2, score, cls = box
                    label = model.names.get(int(cls), 'unknown')
                    if label.lower() == 'fire':
                        detections.append((
                            [x1, y1, x2, y2],  # bounding box
                            float(score)       # confidence
                        ))
        return detections

    except Exception as e:
        print(f"❌ detect_fire: Lỗi khi xử lý ảnh: {e}")
        return []
