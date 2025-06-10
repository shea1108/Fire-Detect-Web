from functools import wraps
from flask import session, redirect, url_for

def login_required_redirect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('web.render_new_frontend_page', page='sign-in'))
        return f(*args, **kwargs)
    return wrapper