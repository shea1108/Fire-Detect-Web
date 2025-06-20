from flask import request, jsonify
from backend.extensions import db
from backend.Models.rbac_model import Role, Permission
from backend.Models.rbac_model import role_permissions
# ======== ROLES ========

def get_all_roles():
    roles = Role.query.all()
    data = [
        {"id": r.role_id, "name": r.role_name}
        for r in roles
    ]
    return jsonify({"success": True, "data": data})

def get_one_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"success": False, "message": "Role không tồn tại"}), 404
    return jsonify({
        "success": True,
        "data": {
            "id": role.role_id,
            "name": role.role_name,
        }
    })

def create_role():
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "message": "Thiếu tên vai trò"}), 400
    if Role.query.filter_by(role_name=name).first():
        return jsonify({"success": False, "message": "Vai trò đã tồn tại"}), 400

    try:
        role = Role(role_name=name)
        db.session.add(role)
        db.session.commit()
        return jsonify({"success": True, "message": "Tạo vai trò thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

def update_role(role_id):
    name = request.form.get("name", "").strip()
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"success": False, "message": "Role không tồn tại"}), 404
    if not name:
        return jsonify({"success": False, "message": "Thiếu tên vai trò"}), 400

    try:
        role.role_name = name
        db.session.commit()
        return jsonify({"success": True, "message": "Cập nhật vai trò thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

def soft_delete_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"success": False, "message": "Vai trò không tồn tại"}), 404

    # Không cho xóa admin và user
    if role.role_name in ["admin", "user"]:
        return jsonify({
            "success": False,
            "message": f"Không thể xóa vai trò hệ thống: {role.role_name}"
        }), 403

    try:
        db.session.delete(role)
        db.session.commit()
        return jsonify({"success": True, "message": "Đã xóa vai trò thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500



# ======== PERMISSIONS ========

def get_all_permissions():
    perms = Permission.query.all()
    data = [
        {"id": p.perm_id, "name": p.perm_name, "desc": p.perm_description}
        for p in perms
    ]
    return jsonify({"success": True, "data": data})

def get_one_permission(perm_id):
    perm = Permission.query.get(perm_id)
    if not perm:
        return jsonify({"success": False, "message": "Permission không tồn tại"}), 404
    return jsonify({"success": True, "data": {
        "id": perm.perm_id,
        "name": perm.perm_name,
        "desc": perm.perm_description
    }})

def create_permission():
    name = request.form.get("name", "").strip()
    desc = request.form.get("desc", "").strip()
    if not name:
        return jsonify({"success": False, "message": "Thiếu tên quyền"}), 400
    if Permission.query.filter_by(perm_name=name).first():
        return jsonify({"success": False, "message": "Quyền đã tồn tại"}), 400

    try:
        perm = Permission(perm_name=name, perm_description=desc)
        db.session.add(perm)
        db.session.commit()
        return jsonify({"success": True, "message": "Tạo quyền thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

def update_permission(perm_id):
    name = request.form.get("name", "").strip()
    desc = request.form.get("desc", "").strip()
    perm = Permission.query.get(perm_id)
    if not perm:
        return jsonify({"success": False, "message": "Permission không tồn tại"}), 404
    if not name:
        return jsonify({"success": False, "message": "Thiếu tên quyền"}), 400

    try:
        perm.perm_name = name
        perm.perm_description = desc
        db.session.commit()
        return jsonify({"success": True, "message": "Cập nhật quyền thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

def soft_delete_permission(perm_id):
    perm = Permission.query.get(perm_id)
    if not perm:
        return jsonify({"success": False, "message": "Permission không tồn tại"}), 404
    try:
        db.session.delete(perm)
        db.session.commit()
        return jsonify({"success": True, "message": "Đã xóa quyền thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500





########
def get_permissions_of_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"success": False, "message": "Role không tồn tại"}), 404

    perm_ids = [p.perm_id for p in role.permissions]
    return jsonify({"success": True, "data": perm_ids})


def update_permissions_of_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"success": False, "message": "Role không tồn tại"}), 404

    perm_ids = request.json.get("perm_ids", [])
    if not isinstance(perm_ids, list):
        return jsonify({"success": False, "message": "Dữ liệu không hợp lệ"}), 400

    try:
        role.permissions = Permission.query.filter(Permission.perm_id.in_(perm_ids)).all()
        db.session.commit()
        return jsonify({"success": True, "message": "Cập nhật quyền thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500