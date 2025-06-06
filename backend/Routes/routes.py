from flask import Blueprint, render_template
import os
bp = Blueprint('web', __name__)

@bp.route('/')
def home():
    return render_template('index.html')


# Tự động tạo route cho tất cả template trong admin/
TEMPLATE_FOLDER_FE_NEW = os.path.join(os.path.dirname(__file__), '../../frontend/templates')
@bp.route('/<path:page>')
def render_new_frontend_page(page):

    # if not page.endswith('.html'):
    #     page += '.html'

    full_path = os.path.join(TEMPLATE_FOLDER_FE_NEW, page)
    if os.path.exists(full_path):
        return render_template(page)  # Không có dấu /
    return render_template('404.html'), 404