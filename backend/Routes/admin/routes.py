from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import os
from backend.decorators.auth_decorators import admin_required
from flask import session
from backend.Models.users_model import User
from backend.Models.rbac_model import Role
from sqlalchemy.orm import joinedload
from backend.extensions import db

bp = Blueprint('admin_routes', __name__, url_prefix='/admin')

TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), '../../../frontend/templates/admin')

# Inject trực tiếp từ session
@bp.context_processor
def inject_user_from_session():
    return dict(
        user_name=session.get("user_name"),
        user_avatar=session.get("user_avatar") or "/static/admin/assets/images/users/user.jpg"
    )

########### User Manager ROUTES ###########

# Route GỐC của admin: Sẽ chuyển hướng đến trang user_list
@bp.route('/')
@admin_required
def index():
    # 'admin_routes.user_list' là tên của blueprint và hàm xử lý trang user
    return redirect(url_for('admin_routes.user_list'))

# Route chính thức cho trang danh sách user
@bp.route('/users')
@admin_required
def user_list():
    # Lấy trạng thái từ query param, mặc định là 'active'
    status = request.args.get('status', 'active')
    
    # Chuyển đổi trạng thái sang boolean
    is_active = (status == 'active')
    
    # Truy vấn users dựa trên trạng thái
    users_query = User.query.filter(User.user_status == is_active)\
                            .options(joinedload(User.roles))\
                            .order_by(User.user_id)
    all_users = users_query.all()
    
    all_roles = Role.query.all()
    role_colors = {'admin': 'bg-danger', 'user': 'bg-primary', 'police': 'bg-success', 'guest': 'bg-secondary'}
    
    return render_template('admin/user_manager.html', 
                           users=all_users, 
                           roles=all_roles, 
                           role_colors=role_colors,
                           current_status=status)


@bp.route('/users/update_roles', methods=['POST'])
@admin_required
def update_user_roles():
    data = request.get_json()
    if not data or 'user_id' not in data or 'role_ids' not in data:
        return jsonify({'status': 'error', 'message': 'Dữ liệu không hợp lệ.'}), 400

    user_id = data.get('user_id')
    role_ids = data.get('role_ids', []) # Nhận một danh sách

    user_to_update = User.query.get(user_id)
    if not user_to_update:
        return jsonify({'status': 'error', 'message': 'Không tìm thấy người dùng.'}), 404

    try:
        selected_roles = Role.query.filter(Role.role_id.in_(role_ids)).all()
        user_to_update.roles = selected_roles
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Đã cập nhật vai trò cho {user_to_update.user_name}.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Lỗi server: {str(e)}'}), 500
    


# --- 1. ROUTE LẤY DỮ LIỆU CỦA MỘT USER (CHO MODAL EDIT) ---
@bp.route('/users/<int:user_id>/data', methods=['GET'])
@admin_required
def get_user_data(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user_id': user.user_id,
        'user_name': user.user_name,
        'user_email': user.user_email,
        'user_phone_num': user.user_phone_num,
        'user_status': user.user_status
    })

# --- 2. ROUTE CẬP NHẬT THÔNG TIN USER (KHI SUBMIT MODAL EDIT) ---
@bp.route('/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data or 'user_name' not in data or 'user_email' not in data:
        return jsonify({'status': 'error', 'message': 'Dữ liệu không hợp lệ.'}), 400

    try:
        user.user_name = data['user_name']
        user.user_email = data['user_email']
        user.user_phone_num = data.get('user_phone_num')
        user.user_status = data.get('user_status', user.user_status)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Cập nhật thông tin người dùng thành công.'})
    except Exception as e:
        db.session.rollback()
        if 'unique constraint' in str(e).lower():
              return jsonify({'status': 'error', 'message': f"Email '{data['user_email']}' đã tồn tại."}), 409
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- 3. ROUTE XÓA MỀM USER ---
@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.user_status = False
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Đã xóa người dùng.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- 4. ROUTE KHÔI PHỤC USER ---
@bp.route('/users/<int:user_id>/restore', methods=['POST'])
@admin_required
def restore_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.user_status = True
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Đã khôi phục người dùng.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


############ MODELS ROUTES STARTS ############
@bp.route("/models", methods=["GET"])
@admin_required
def models_list_page():
    return render_template("admin/admin_models.html")


@bp.route("/models/create", methods=["GET"])
@admin_required
def create_models_page():
    return render_template("admin/admin_models_create.html")


@bp.route("/models/edit/<int:model_id>", methods=["GET"])
@admin_required
def edit_model_page(model_id):
    return render_template("admin/admin_models_edit.html", model_id=model_id)
############ MODELS ROUTES ENDS ############

@bp.route('/<path:page>')
@admin_required
def render_admin_page(page):
    if not page.endswith('.html'):
        page += '.html'

    filename = f"admin/{page}"
    full_path = os.path.join(TEMPLATE_FOLDER, page)
    if os.path.exists(full_path):
        return render_template(filename)
    return f"404 - {filename} not found", 404