from flask import Blueprint, render_template
import os
from flask import Blueprint, render_template, session, redirect, url_for
from backend.utils.auth_utils import login_required_redirect
from backend.Models.users_model import User

bp = Blueprint('web', __name__)

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/profile')
@login_required_redirect
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return render_template('sign-in.html')

    return render_template('profile.html', user=user)


TEMPLATE_FOLDER_FE_NEW = os.path.join(os.path.dirname(__file__), '../../frontend/templates')
@bp.route('/<path:page>')
def render_new_frontend_page(page):

    if not page.endswith('.html'):
        page += '.html'

    full_path = os.path.join(TEMPLATE_FOLDER_FE_NEW, page)
    if os.path.exists(full_path):
        return render_template(page)
    return render_template('404.html'), 404