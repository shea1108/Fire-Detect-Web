from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text  # BẮT BUỘC nếu dùng SQL string

db = SQLAlchemy()

def test_db_connection():
    try:
        db.session.execute(text("SELECT 1"))  # Dùng text()
        print("✅ Kết nối cơ sở dữ liệu thành công!")
    except Exception as e:
        print("❌ Lỗi khi kết nối DB:", e)
