# /app.py
import gevent.monkey
gevent.monkey.patch_all()  # 👈 Patch tất cả thư viện chuẩn trước mọi import khác

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


import os

from backend import create_app, socketio

import logging



# Ẩn lỗi do client ngắt video sớm
logging.getLogger("eventlet.wsgi.server").setLevel(logging.ERROR)


app = create_app()

if __name__ == '__main__':
    # socketio.run(app, debug=True, use_reloader=True, host='127.0.0.1', port=5000)
    # socketio.run(app, debug=True, use_reloader=True, host='192.168.10.8', port=5000, ssl_context=context)
    host = '192.168.1.9' # 127.0.0.1
    port = 5000
    use_ssl = True  # đổi thành False nếu không dùng SSL

    if use_ssl:
        import ssl
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile='certs/cert.pem', keyfile='certs/key.pem')
        print(f'🚀 FireDetect is running with HTTPS at https://{host}:{port}')
        socketio.run(app, debug=True, use_reloader=True, host=host, port=port, ssl_context=context)
    else:
        print(f'🚀 FireDetect is running at http://{host}:{port}')
        socketio.run(app, debug=True, use_reloader=True, host=host, port=port)


