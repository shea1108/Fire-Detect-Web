import os
from backend.Routes import routes
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from backend.extensions import db, bcrypt, socketio

def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

    socketio.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    CORS(app)

    # Đảm bảo models đã được import để SQLAlchemy tạo bảng
    from backend.Models.users_model import User

    with app.app_context():
        db.create_all()

    from backend.Routes import auth, predict, socketio as socket
    from backend.Routes.admin import routes as admin_routes


    app.register_blueprint(auth.bp)
    app.register_blueprint(routes.bp)
    app.register_blueprint(predict.bp)
    app.register_blueprint(admin_routes.bp)  # ✅ đăng ký admin
    socket.register_socketio(socketio)

    return app
