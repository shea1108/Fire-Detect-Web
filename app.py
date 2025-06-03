import os
from dotenv import load_dotenv, dotenv_values
from backend import create_app, socketio

load_dotenv()  # Nạp biến môi trường từ file .env

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=False, host='127.0.0.1', port=5000)

    # host = os.getenv("HOST", "127.0.0.1")      # Mặc định là 0.0.0.0 nếu không có
    # port = int(os.getenv("PORT", "5000"))      # Mặc định là 5000 nếu không có
    # socketio.run(app, debug=True, host=host, port=port, use_reloader=False)
