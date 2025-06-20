from flask import Blueprint
from backend.Controllers.admin import rbac_controller
from backend.decorators.auth_decorators import admin_required

bp = Blueprint("admin_rbac", __name__, url_prefix="/api/admin/rbac")

# ===== ROLES =====
@bp.route("/roles/get-all", methods=["GET"])
@admin_required
def get_all_roles():
    return rbac_controller.get_all_roles()

@bp.route("/roles/get-one/<int:role_id>", methods=["GET"])
@admin_required
def get_one_role(role_id):
    return rbac_controller.get_one_role(role_id)

@bp.route("/roles/create", methods=["POST"])
@admin_required
def create_role():
    return rbac_controller.create_role()

@bp.route("/roles/update/<int:role_id>", methods=["POST"])
@admin_required
def update_role(role_id):
    return rbac_controller.update_role(role_id)

@bp.route("/roles/delete/<int:role_id>", methods=["PUT"])
@admin_required
def delete_role(role_id):
    return rbac_controller.soft_delete_role(role_id)


# ===== PERMISSIONS =====
@bp.route("/permissions/get-all", methods=["GET"])
@admin_required
def get_all_permissions():
    return rbac_controller.get_all_permissions()

@bp.route("/permissions/get-one/<int:perm_id>", methods=["GET"])
@admin_required
def get_one_permission(perm_id):
    return rbac_controller.get_one_permission(perm_id)

@bp.route("/permissions/create", methods=["POST"])
@admin_required
def create_permission():
    return rbac_controller.create_permission()

@bp.route("/permissions/update/<int:perm_id>", methods=["POST"])
@admin_required
def update_permission(perm_id):
    return rbac_controller.update_permission(perm_id)

@bp.route("/permissions/delete/<int:perm_id>", methods=["PUT"])
@admin_required
def delete_permission(perm_id):
    return rbac_controller.soft_delete_permission(perm_id)
