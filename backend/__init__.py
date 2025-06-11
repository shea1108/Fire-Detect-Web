import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta

# Import các extensions từ file extensions.py
from backend.extensions import db, bcrypt, socketio, oauth, mail

# Import các Blueprints (routes)
from backend.Routes import routes
from backend.Routes import auth
from backend.Routes import predict
from backend.Routes import socketio as socket
from backend.Routes.admin import routes as admin_routes
from backend.Routes.models import bp as models_bp
from backend.Routes.notification import bp as notification_bp
from backend.Routes import user

# Import Models để db.create_all() có thể thấy chúng
# Giả sử bạn có file __init__.py trong thư mục Models để import như thế này
from backend.Models import *

def create_app():
    # 1. Load biến môi trường ĐẦU TIÊN
    load_dotenv()

    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    
    # 2. Cấu hình app từ các biến môi trường
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.permanent_session_lifetime = timedelta(days=7)

    # 3. Cấu hình MAIL
    MAIL_ENABLED = os.getenv("MAIL_ENABLED", "True").lower() == "true"
    app.config["MAIL_ENABLED"] = MAIL_ENABLED
    app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
    app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT") or 587)
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", "True").lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL", "False").lower() == 'true'
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")
    
    # 4. Khởi tạo các extensions với app
    db.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app)
    oauth.init_app(app)
    mail.init_app(app) # Chỉ gọi một lần ở đây
    CORS(app)

    # In trạng thái cấu hình Mail để dễ debug
    if MAIL_ENABLED:
        if all([app.config['MAIL_SERVER'], app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']]):
            print("✅ [MAIL] Gửi email đã được BẬT.")
            print(f"👉 SMTP: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']} | Sender: {app.config['MAIL_DEFAULT_SENDER']}")
        else:
            print("⚠️ [MAIL] Gửi email BẬT nhưng thiếu thông tin cấu hình. Kiểm tra file .env.")
    else:
        print("🚫 [MAIL] Gửi email đã bị TẮT (MAIL_ENABLED=False).")

    # 5. Tạo các bảng trong database nếu chưa có
    with app.app_context():
        db.create_all()

    # 6. Đăng ký các Blueprints
    app.register_blueprint(models_bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(routes.bp)
    app.register_blueprint(predict.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(user.user_bp)
    
    # Đăng ký SocketIO events
    socket.register_socketio(socketio)

    return app
