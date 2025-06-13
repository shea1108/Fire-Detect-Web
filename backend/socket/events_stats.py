# backend/socket/events_stats.py
from flask_socketio import emit
from backend.socket.common import perf_monitor
import time

def register_stats_events(socketio):
    @socketio.on('get_stats')
    def handle_get_stats():
        stats = perf_monitor.get_stats()
        stats['server_time'] = time.strftime('%H:%M:%S')
        emit('stats', stats)
