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
from backend.Models.logbboxs_model import LogBbox   
from backend.Models.flatforms_model import Platform
from backend.Models.notifications_model import Notification
from backend.Models.notification_models_model import NotificationPlatform
from backend.Models.user_flatform_model import UserPlatform

from backend.Routes import auth, predict, socketio as socket
from backend.Routes.admin import routes as admin_routes

from backend.Routes.models import bp as models_bp

def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

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

    return app