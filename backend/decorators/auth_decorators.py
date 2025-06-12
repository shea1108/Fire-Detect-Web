# backend/decorators/auth_decorators.py
from functools import wraps
from flask import session, render_template

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return render_template('401.html'), 401
        if 'admin' not in session.get('user_role', []):
            return render_template('403.html'), 403
        return f(*args, **kwargs)
    return decorated

