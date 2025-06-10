# backend/extensions.py
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth



db = SQLAlchemy()
bcrypt = Bcrypt()
socketio = SocketIO()
mail = Mail()
oauth = OAuth()