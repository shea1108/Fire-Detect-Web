# backend/utils/auth_utils.py
from functools import wraps
from flask import session, redirect, url_for

def login_required_redirect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            session['swal_message'] = {
                'title': 'Yêu cầu đăng nhập',
                'text': 'Bạn cần đăng nhập để sử dụng tính năng này.',
                'icon': 'info'
            }
            return redirect(url_for('web.sign_in'))
        return f(*args, **kwargs)
    return wrapper