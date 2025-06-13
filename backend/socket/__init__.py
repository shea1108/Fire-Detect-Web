# === backend/socket/__init__.py ===
# Đây là entrypoint chính để gọi tất cả event handler
from .common import perf_monitor
from .events_connection import register_connection_events
from .events_model import register_model_events
from .events_stats import register_stats_events
from .events_frame import register_frame_events
from .events_device import register_device_events


def register_socketio(socketio):
    register_connection_events(socketio)
    register_model_events(socketio)
    register_stats_events(socketio)
    register_frame_events(socketio, perf_monitor)
    register_device_events(socketio)
