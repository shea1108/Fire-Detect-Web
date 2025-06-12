import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RESET_TOKEN_EXPIRY_SECONDS = int(os.getenv('RESET_TOKEN_EXPIRY_SECONDS', 300))  # mặc định 5 phút
    REGISTER_OTP_EXPIRY_SECONDS = int(os.getenv('REGISTER_OTP_EXPIRY_SECONDS', 300))  # mặc định 5 phút
