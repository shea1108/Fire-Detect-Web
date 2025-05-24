# 🔥 Fire Detection System with YOLOv8

A web-based real-time fire detection system using [YOLOv8](https://github.com/ultralytics/ultralytics) for image, video, and camera stream inputs.  
The project includes a modern web interface (Flask) and supports running inference with your custom-trained YOLOv8 fire model.

## ⭐ Features

- Detect fire in **images**, **videos**, and **live camera** streams.
- Support custom YOLOv8 weights (e.g. `best.pt`).
- Realtime detection with bounding boxes and confidence.
- User-friendly web interface.
- Works with CPU or GPU (if available).

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS,
- **AI Model:** YOLOv8 (Ultralytics)
- **Database:** PostgreSQL

## 📂 Project Structure

```plaintext
├── app.py                    # Flask backend
├── requirements.txt
├── static/                   # CSS, JS, frontend assets
├── templates/                # HTML templates
├── yolov8/                   # YOLOv8 model & inference code
│   └── best.pt               # Your trained model weights
├── README.md
└── ...
