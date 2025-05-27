from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv
from ultralytics import YOLO
from PIL import Image
import base64, io, os, uuid
import eventlet
from flask_socketio import SocketIO, emit


# --- Load .env ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

# --- Init Flask ---
app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")
# --- Extensions ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app)

# --- YOLO Model ---
model = YOLO('../Yolo/best.pt')

# --- User Model ---
class User(db.Model):
    __tablename__ = 'USERS'
    user_id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(120), unique=True, nullable=False)
    user_password = db.Column(db.String(200), nullable=False)
    user_phone_num = db.Column(db.String(20))
    user_role = db.Column(db.String(20), nullable=False)

# --- Auth Routes ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        print("Dữ liệu nhận từ client:", data)

        # Kiểm tra thiếu dữ liệu
        required_fields = ['user_name', 'user_email', 'user_password', 'user_role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Thiếu trường {field}"}), 400

        if User.query.filter_by(user_email=data['user_email']).first():
            return jsonify({"error": "Email đã được sử dụng"}), 400

        hashed_pw = bcrypt.generate_password_hash(data['user_password']).decode('utf-8')
        user = User(
            user_name=data['user_name'],
            user_email=data['user_email'],
            user_password=hashed_pw,
            user_phone_num=data.get('user_phone_num', ''),
            user_role=data['user_role']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Đăng ký thành công"}), 201

    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"error": "Lỗi máy chủ"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(user_email=data['user_email']).first()
    if user and bcrypt.check_password_hash(user.user_password, data['user_password']):
        return jsonify({"message": "Đăng nhập thành công"})
    return jsonify({"error": "Sai email hoặc mật khẩu"}), 401


@socketio.on('frame')
def handle_frame(data):
    # Decode the base64 image
    image_data = base64.b64decode(data.split(',')[1])
    image = Image.open(io.BytesIO(image_data)).convert('RGB')

    # Perform detection using your YOLO model
    results = model(image)
    detections = []

    for result in results:
        for box in result.boxes.data.tolist():
            x1, y1, x2, y2, score, cls = box
            detections.append({
                'bbox': [x1, y1, x2, y2],
                'confidence': float(score),
                'class_id': int(cls),
                'label': model.names[int(cls)]
            })

    # Send detections back to the client
    emit('detections', {'detections': detections})


# --- Giao diện ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/camera')
def camera():
    return render_template('detectcamera.html')

@app.route('/picture')
def picture():
    return render_template('detectpicture.html')

@app.route('/video')
def video():
    return render_template('detectvideo.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

# --- Nhận diện ảnh ---
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        image = Image.open(file.stream).convert('RGB')
        results = model(image)
        detections = []

        for result in results:
            for box in result.boxes.data.tolist():
                x1, y1, x2, y2, score, cls = box
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': float(score),
                    'class_id': int(cls),
                    'label': model.names[int(cls)]
                })

        return jsonify({'detections': detections})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/detect-frame', methods=['POST'])
def detect_frame():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400

    try:
        image_data = data['image'].split(',')[1]
        img_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')

        results = model(image)
        detections = []

        for result in results:
            for box in result.boxes.data.tolist():
                x1, y1, x2, y2, score, cls = box
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': float(score),
                    'class_id': int(cls),
                    'label': model.names[int(cls)]
                })

        return jsonify({'detections': detections})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Tạo bảng nếu chưa có ---
with app.app_context():
    db.create_all()

# --- Chạy ứng dụng ---
if __name__ == '__main__':
    socketio.run(app, debug=True)
