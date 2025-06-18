# /app.py

import os
from dotenv import load_dotenv, dotenv_values
from backend import create_app, socketio
import ssl

# context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain(certfile='certs/cert.pem', keyfile='certs/key.pem')
# load_dotenv()  # Nạp biến môi trường từ file .env
import eventlet
eventlet.monkey_patch()

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=True, host='127.0.0.1', port=5000)
    # socketio.run(app, debug=True, use_reloader=True, host='192.168.10.4', port=5000, ssl_context=context)


