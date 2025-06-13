# backend/utils/auth_utils.py
from functools import wraps
from flask import session, redirect, url_for

def login_required_redirect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('sign-in.html')
        return f(*args, **kwargs)
    return wrapper