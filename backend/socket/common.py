# backend/socket/common.py
import time
from collections import deque
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.frame_count = 0
        self.detection_count = 0
        self.start_time = None
        self.last_log_time = time.time()
        self.log_interval = 5
        self.total_data_received = 0
        self.total_recv_time = 0
        self.timestamps = deque(maxlen=30)

    def update(self, detections_count, data_size_kb=None, recv_time=None):
        self.timestamps.append(time.time())
        if self.start_time is None:
            self.start_time = time.time()
        self.frame_count += 1
        self.detection_count += detections_count
        if data_size_kb and recv_time:
            self.total_data_received += data_size_kb
            self.total_recv_time += recv_time
        if time.time() - self.last_log_time >= self.log_interval:
            self.log_stats()
            self.last_log_time = time.time()

    def log_stats(self):
        stats = self.get_stats()
        if stats:
            logger.info(f"⚙️ Stats - FPS: {stats['fps']}, Detections: {stats['total_detections']}, Frames: {stats['frames_processed']}")

    def get_stats(self):
        if self.start_time is None:
            return {}
        if len(self.timestamps) >= 2:
            elapsed = self.timestamps[-1] - self.timestamps[0]
            fps = (len(self.timestamps) - 1) / elapsed if elapsed > 0 else 0
        else:
            fps = 0
        avg_speed = (self.total_data_received / self.total_recv_time) if self.total_recv_time > 0 else 0

        return {
            'frames_processed': self.frame_count,
            'total_detections': self.detection_count,
            'fps': round(fps, 2),
            'avg_network_speed_kbps': round(avg_speed, 2)
        }

# Khởi tạo 1 instance duy nhất
perf_monitor = PerformanceMonitor()
