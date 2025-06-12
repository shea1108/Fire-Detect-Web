from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt="password-reset")

def verify_reset_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        max_age = current_app.config['RESET_TOKEN_EXPIRY_SECONDS']
        email = s.loads(token, salt="password-reset", max_age=max_age)
    except Exception:
        return None
    return email
