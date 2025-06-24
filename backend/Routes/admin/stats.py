# /api/admin/stats.py
from flask import Blueprint, jsonify, request
from backend.extensions import db
from backend.Models.users_model import User
from backend.Models.logs_model import Log
from backend.Models.models_model import Model
from backend.Models.notifications_model import Notification
from sqlalchemy import func, cast, Date


bp = Blueprint('admin_stats', __name__, url_prefix='/api/admin/stats')

@bp.route('/overview', methods=['GET'])
def get_overview_stats():
    return jsonify({
        "success": True,
        "data": {
            "users": db.session.query(User).count(),    
            "models": db.session.query(Model).count(),
            "logs": db.session.query(Log).count(),
            "notifications": db.session.query(Notification).count()
        }
    })

from sqlalchemy import func, cast, Date, text

@bp.route("/logs-by-date", methods=["GET"])
def logs_by_date():
    range_type = request.args.get("range", "7d")
    from datetime import datetime, timedelta

    now = datetime.now()
    if range_type == "1d":
        start_date = now - timedelta(days=1)
        group_format = "day"
    elif range_type == "3d":
        start_date = now - timedelta(days=3)
        group_format = "day"
    elif range_type == "7d":
        start_date = now - timedelta(days=7)
        group_format = "day"
    elif range_type in ["1m", "3m", "6m", "1y"]:
        days = {"1m": 30, "3m": 90, "6m": 180, "1y": 365}[range_type]
        start_date = now - timedelta(days=days)
        group_format = "month"
    else:
        start_date = now - timedelta(days=7)
        group_format = "day"

    if group_format == "day":
        results = (
            db.session.query(cast(Log.log_create_at, Date), func.count())
            .filter(Log.log_create_at >= start_date)
            .group_by(cast(Log.log_create_at, Date))
            .order_by(cast(Log.log_create_at, Date))
            .all()
        )
        data = [{"date": str(r[0]), "count": r[1]} for r in results]
    else:  # group by month
        results = (
            db.session.query(func.to_char(Log.log_create_at, 'YYYY-MM'), func.count())
            .filter(Log.log_create_at >= start_date)
            .group_by(func.to_char(Log.log_create_at, 'YYYY-MM'))
            .order_by(func.to_char(Log.log_create_at, 'YYYY-MM'))
            .all()
        )
        data = [{"date": r[0], "count": r[1]} for r in results]

    return jsonify({"success": True, "data": data})


@bp.route("/notifications-by-date", methods=["GET"])
def notifications_by_date():
    range_type = request.args.get("range", "7d")

    from datetime import datetime, timedelta

    now = datetime.now()
    if range_type == "1d":
        start_date = now - timedelta(days=1)
        group_format = "day"
    elif range_type == "3d":
        start_date = now - timedelta(days=3)
        group_format = "day"
    elif range_type == "7d":
        start_date = now - timedelta(days=7)
        group_format = "day"
    elif range_type in ["1m", "3m", "6m", "1y"]:
        days = {"1m": 30, "3m": 90, "6m": 180, "1y": 365}[range_type]
        start_date = now - timedelta(days=days)
        group_format = "month"
    else:
        start_date = now - timedelta(days=7)
        group_format = "day"

    if group_format == "day":
        results = (
            db.session.query(cast(Notification.noti_create_at, Date), func.count())
            .filter(Notification.noti_create_at >= start_date)
            .group_by(cast(Notification.noti_create_at, Date))
            .order_by(cast(Notification.noti_create_at, Date))
            .all()
        )
        data = [{"date": str(r[0]), "count": r[1]} for r in results]
    else:  # group by month
        results = (
            db.session.query(func.to_char(Notification.noti_create_at, 'YYYY-MM'), func.count())
            .filter(Notification.noti_create_at >= start_date)
            .group_by(func.to_char(Notification.noti_create_at, 'YYYY-MM'))
            .order_by(func.to_char(Notification.noti_create_at, 'YYYY-MM'))
            .all()
        )
        data = [{"date": r[0], "count": r[1]} for r in results]

    return jsonify({"success": True, "data": data})
