# yolo_infer.py
import onnxruntime as ort
import numpy as np
import cv2

class YOLODetector:
    def __init__(self, model_path, conf_threshold=0.4):
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = (640, 640)
        self.conf_threshold = conf_threshold

    def letterbox(self, img, new_shape=(640, 640), color=(114, 114, 114)):
        shape = img.shape[:2]  # current shape [height, width]
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        dw = new_shape[1] - new_unpad[0]  # width padding
        dh = new_shape[0] - new_unpad[1]  # height padding
        dw /= 2  # divide padding into 2 sides
        dh /= 2

        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        return img, r, dw, dh

    def preprocess(self, frame):
        self.orig = frame.copy()
        self.h0, self.w0 = frame.shape[:2]
        img, self.r, self.dw, self.dh = self.letterbox(frame, self.input_shape)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))[np.newaxis, ...]
        return img

    def postprocess(self, outputs):
        preds = outputs[0]  # chưa [0][0], để xem toàn bộ
        print("DEBUG: outputs[0] shape =", preds.shape)
        print("DEBUG: sample prediction =", preds[0][:10])  # In 10 giá trị đầu dòng đầu tiên
        exit() 


    def detect(self, frame):
        input_tensor = self.preprocess(frame)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        boxes = self.postprocess(outputs)

        for (x1, y1, x2, y2, score, class_id) in boxes:
            label = f"{score:.2f}"
            cv2.rectangle(self.orig, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(self.orig, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return self.orig
