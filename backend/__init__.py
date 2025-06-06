# backend/__init__.py

import os
from backend.Routes import routes
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from backend.extensions import db, bcrypt, socketio

from backend.Models.users_model import User
from backend.Models.devices_model import Device 
from backend.Models.models_model import Model   
from backend.Models.logs_model import Log       

from backend.Models.flatforms_model import Platform
from backend.Models.notifications_model import Notification
from backend.Models.notification_models_model import NotificationPlatform
from backend.Models.user_flatform_model import UserPlatform

from backend.Routes.notification import bp as notification_bp
from backend.Routes import auth, predict, socketio as socket
from backend.Routes.admin import routes as admin_routes
from backend.Routes.models import bp as models_bp


#Session
from datetime import timedelta  # thêm import

#MAIL
from backend.extensions import mail


def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

    # >>>>>>>>>>>>>>Session
    app.permanent_session_lifetime = timedelta(days=7)  # 👉 giữ session 7 ngày

    # >>>>>>>>>>>>>>MAIL
    MAIL_ENABLED = os.getenv("MAIL_ENABLED", "True") == "True"
    app.config["MAIL_ENABLED"] = MAIL_ENABLED
    app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
    app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT"))
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS") == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL") == 'True'
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")
    if not os.getenv("MAIL_SERVER") and MAIL_ENABLED:
        print("⚠️ Cảnh báo: MAIL_ENABLED=True nhưng chưa cấu hình mail server.")

    # Init mail sau khi config xong
    mail.init_app(app)
    # 🔔 Thông báo trạng thái kết nối mail
    if MAIL_ENABLED:
        if app.config['MAIL_SERVER'] and app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
            print("✅ [MAIL] Gửi email đã được BẬT.")
            print(f"👉 SMTP: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']} | Sender: {app.config['MAIL_DEFAULT_SENDER']}")
        else:
            print("⚠️ [MAIL] Gửi email BẬT nhưng thiếu thông tin cấu hình. Kiểm tra biến môi trường.")
    else:
        print("🚫 [MAIL] Gửi email đã bị TẮT (MAIL_ENABLED=False).")




    socketio.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(models_bp)

    app.register_blueprint(auth.bp)
    app.register_blueprint(routes.bp)
    app.register_blueprint(predict.bp)
    app.register_blueprint(admin_routes.bp)
    socket.register_socketio(socketio)
    app.register_blueprint(notification_bp)
    return app