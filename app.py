from flask import Flask
from backend.config import Config
from backend.extensions import db
from backend.extensions import test_db_connection

from backend.routes.web_routes import web_bp
from backend.routes.admin_routes import admin_bp



app = Flask(__name__, static_folder="frontend", template_folder="frontend")

# Cấu hình từ .env
app.config.from_object(Config)

# Khởi tạo DB
db.init_app(app)

# Blueprint
app.register_blueprint(web_bp)
app.register_blueprint(admin_bp)

# 👉 Kiểm tra kết nối DB khi app khởi động
with app.app_context():
    test_db_connection()


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8000)
