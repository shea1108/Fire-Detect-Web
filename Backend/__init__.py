import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta

from backend.extensions import db, bcrypt, socketio, oauth, mail
from backend.Models.users_model import User


def create_app():
    # 1. Load biến môi trường ĐẦU TIÊN
    load_dotenv()

    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    
    # 2. Cấu hình app từ các biến môi trường
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.permanent_session_lifetime = timedelta(days=7)

    # Cấu hình MAIL
    MAIL_ENABLED = os.getenv("MAIL_ENABLED", "True") == "True"
    app.config["MAIL_ENABLED"] = MAIL_ENABLED
    app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
    app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT") or 587)
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS") == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL") == 'True'
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")
    
    if MAIL_ENABLED:
        if app.config['MAIL_SERVER'] and app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
            print("✅ [MAIL] Gửi email đã được BẬT.")
            print(f"👉 SMTP: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']} | Sender: {app.config['MAIL_DEFAULT_SENDER']}")
        else:
            print("⚠️ [MAIL] Gửi email BẬT nhưng thiếu thông tin cấu hình. Kiểm tra biến môi trường.")
    else:
        print("🚫 [MAIL] Gửi email đã bị TẮT (MAIL_ENABLED=False).")



    db.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app)
    oauth.init_app(app)
    mail.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()


    from backend.Routes import routes
    from backend.Routes import auth
    from backend.Routes import predict
    from backend.Routes import socketio as socket
    from backend.Routes.admin import routes as admin_routes
    from backend.Routes.models import bp as models_bp
    from backend.Routes.notification import bp as notification_bp
    from backend.Routes.user import user_bp


    app.register_blueprint(models_bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(routes.bp)
    app.register_blueprint(predict.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(user_bp)
    
    socket.register_socketio(socketio)

    return app