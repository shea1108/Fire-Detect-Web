# backend/socket/events_connection.py


from flask import request
from flask_socketio import emit
import logging

logger = logging.getLogger(__name__)

def register_connection_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        emit('status', {'message': 'Connected to fire detection server'})

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")
