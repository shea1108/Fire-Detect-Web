import os
from flask import Blueprint, render_template, session, redirect, url_for
from backend.utils.auth_utils import login_required_redirect
from backend.Models.users_model import User

bp = Blueprint('web', __name__)

# Giả định đường dẫn đến thư mục templates
TEMPLATE_FOLDER_FE_NEW = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'templates'))

@bp.route('/')
def home():
    return render_template('index.html', user_session=session)

@bp.route('/profile')
@login_required_redirect
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return redirect(url_for('web.render_new_frontend_page', page='sign-in'))

    return render_template('profile.html', user=user, user_session=session)

@bp.route('/<path:page>')
def render_new_frontend_page(page):

    if not page.endswith('.html'):
        page += '.html'

    full_path = os.path.join(TEMPLATE_FOLDER_FE_NEW, page)
    if os.path.exists(full_path):

        return render_template(page, user_session=session)
    
    return render_template('404.html', user_session=session), 404
