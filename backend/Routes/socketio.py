from flask_socketio import emit
from PIL import Image
import base64
import io
import numpy as np
from ultralytics import YOLO
import cv2
import logging
import time
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load YOLO model once at startup
try:
    model = YOLO('Yolo/29.5_v4_caitien.pt')
    model.to('cuda')  # ép sử dụng GPU
    logger.info("YOLO model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load YOLO model: {e}")
    model = None

def register_socketio(socketio):
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected")
        emit('status', {'message': 'Connected to fire detection server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected")
    
    @socketio.on('frame')
    def handle_frame(data):
        try:
            if model is None:
                emit('error', {'message': 'YOLO model not loaded'})
                return
            
            # Validate data format
            if not data or not isinstance(data, str):
                emit('error', {'message': 'Invalid frame data'})
                return
            
            # Decode base64 image
            try:
                if ',' in data:
                    image_data = base64.b64decode(data.split(',')[1])
                else:
                    image_data = base64.b64decode(data)
            except Exception as e:
                logger.error(f"Failed to decode base64 data: {e}")
                emit('error', {'message': 'Failed to decode image data'})
                return
            
            # Convert to PIL Image
            try:
                image = Image.open(io.BytesIO(image_data)).convert('RGB')
                
                # Optional: Resize image for faster processing if too large
                max_size = 640
                if max(image.size) > max_size:
                    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
            except Exception as e:
                logger.error(f"Failed to process image: {e}")
                emit('error', {'message': 'Failed to process image'})
                return
            
            # Run YOLO detection
            try:
                # Configure YOLO parameters
                results = model(
                    image,
                    conf=0.25,      # Confidence threshold
                    iou=0.45,       # IoU threshold for NMS
                    max_det=100,    # Maximum detections
                    verbose=False   # Suppress YOLO output
                )
                
                detections = []
                
                # Process results
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes.data.tolist():
                            if len(box) >= 6:  # Ensure we have all required values
                                x1, y1, x2, y2, score, cls = box[:6]
                                
                                # Validate coordinates
                                if all(isinstance(coord, (int, float)) for coord in [x1, y1, x2, y2]):
                                    detection = {
                                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                        'confidence': float(score),
                                        'class_id': int(cls),
                                        'label': model.names.get(int(cls), f'Class_{int(cls)}')
                                    }
                                    detections.append(detection)
                
                # Log detection results
                if detections:
                    logger.info(f"Detected {len(detections)} objects")
                    for det in detections:
                        logger.info(f"  - {det['label']}: {det['confidence']:.2f}")
                
                # Send results back to client
                emit('detections', {
                    'detections': detections,
                    'total_count': len(detections),
                    'timestamp': int(time.time()), #socketio.server.manager.timestamp()
                })
                
            except Exception as e:
                logger.error(f"YOLO detection failed: {e}")
                emit('error', {'message': 'Detection failed'})
                return
                
        except Exception as e:
            logger.error(f"Unexpected error in handle_frame: {e}")
            emit('error', {'message': 'Server error occurred'})

# Optional: Additional utility functions for fire detection optimization

def preprocess_image_for_fire_detection(image):
    """
    Optional preprocessing for better fire detection
    """
    try:
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Optional: Apply fire-specific preprocessing
        # Example: Enhance red/orange channels for fire detection
        # This is just an example - adjust based on your model's needs
        
        # Convert back to PIL
        return Image.fromarray(img_array)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return image

def filter_fire_detections(detections, min_confidence=0.5):
    """
    Filter detections to focus on high-confidence fire detections
    """
    filtered = []
    for det in detections:
        if det['confidence'] >= min_confidence:
            # Additional filtering logic can be added here
            # For example, filter by label if you have specific fire classes
            if 'fire' in det['label'].lower() or 'flame' in det['label'].lower():
                filtered.append(det)
    return filtered

# Health check function
def check_model_health():
    """
    Check if the YOLO model is loaded and working
    """
    if model is None:
        return False, "Model not loaded"
    
    try:
        # Create a small test image
        test_image = Image.new('RGB', (64, 64), color='red')
        results = model(test_image, verbose=False)
        return True, "Model is healthy"
    except Exception as e:
        return False, f"Model error: {e}"

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.frame_count = 0
        self.detection_count = 0
        self.start_time = None
    
    def update(self, detections_count):
        if self.start_time is None:
            import time
            self.start_time = time.time()
        
        self.frame_count += 1
        self.detection_count += detections_count
    
    def get_stats(self):
        if self.start_time is None:
            return {}
        
        import time
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        return {
            'frames_processed': self.frame_count,
            'total_detections': self.detection_count,
            'fps': round(fps, 2),
            'uptime_seconds': round(elapsed, 2)
        }

# Global performance monitor instance
perf_monitor = PerformanceMonitor()

# Enhanced register function with monitoring
def register_socketio_with_monitoring(socketio):
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected")
        health_ok, health_msg = check_model_health()
        emit('status', {
            'message': 'Connected to fire detection server',
            'model_health': health_ok,
            'health_details': health_msg
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected")
    
    @socketio.on('get_stats')
    def handle_get_stats():
        stats = perf_monitor.get_stats()
        emit('stats', stats)
    
    @socketio.on('frame')
    def handle_frame(data):
        try:
            if model is None:
                emit('error', {'message': 'YOLO model not loaded'})
                return
            
            # Validate data format
            if not data or not isinstance(data, str):
                emit('error', {'message': 'Invalid frame data'})
                return
            
            # Decode base64 image
            try:
                if ',' in data:
                    image_data = base64.b64decode(data.split(',')[1])
                else:
                    image_data = base64.b64decode(data)
            except Exception as e:
                logger.error(f"Failed to decode base64 data: {e}")
                emit('error', {'message': 'Failed to decode image data'})
                return
            
            # Convert to PIL Image
            try:
                image = Image.open(io.BytesIO(image_data)).convert('RGB')
                
                # Optional preprocessing
                image = preprocess_image_for_fire_detection(image)
                
                # Resize for performance if needed
                max_size = 640
                if max(image.size) > max_size:
                    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
            except Exception as e:
                logger.error(f"Failed to process image: {e}")
                emit('error', {'message': 'Failed to process image'})
                return
            
            # Run YOLO detection
            try:
                results = model(
                    image,
                    conf=0.25,
                    iou=0.45,
                    max_det=100,
                    verbose=False
                )
                
                detections = []
                
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes.data.tolist():
                            if len(box) >= 6:
                                x1, y1, x2, y2, score, cls = box[:6]
                                
                                if all(isinstance(coord, (int, float)) for coord in [x1, y1, x2, y2]):
                                    detection = {
                                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                        'confidence': float(score),
                                        'class_id': int(cls),
                                        'label': model.names.get(int(cls), f'Class_{int(cls)}')
                                    }
                                    detections.append(detection)
                
                # Optional: Filter for fire-specific detections
                # detections = filter_fire_detections(detections, min_confidence=0.5)
                
                # Update performance monitor
                perf_monitor.update(len(detections))
                
                # Log detection results
                if detections:
                    logger.info(f"Detected {len(detections)} objects")
                
                # Send results back to client
                emit('detections', {
                    'detections': detections,
                    'total_count': len(detections),
                    'timestamp': int(time.time()), #socketio.server.manager.timestamp(),
                    'processing_stats': {
                        'image_size': image.size,
                        'detections_found': len(detections)
                    }
                })
                
            except Exception as e:
                logger.error(f"YOLO detection failed: {e}")
                emit('error', {'message': 'Detection failed'})
                return
                
        except Exception as e:
            logger.error(f"Unexpected error in handle_frame: {e}")
            emit('error', {'message': 'Server error occurred'})
