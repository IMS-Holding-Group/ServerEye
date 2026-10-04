from flask import Blueprint, jsonify, render_template, session

from models.alert_model import AlertModel
from models.metric_model import MetricModel
from models.server_model import ServerModel
from services.alert_service import derive_server_status
from utils.datetime_fmt import format_arabic_datetime, format_arabic_datetime_html
from utils.security import generate_csrf_token, role_required

dashboard_bp = Blueprint('dashboard', __name__)


def _server_card(server):
    latest = MetricModel.get_latest(server['id'])
    status = derive_server_status(server['id'], latest)
    return {
        'id': server['id'],
        'name': server['name'],
        'os_type': server['os_type'],
        'host_address': server['host_address'],
        'status': status,
        'is_in_baseline': bool(server.get('is_in_baseline')),
        'cpu': round(latest['cpu_percent'], 1) if latest else None,
        'ram': round(latest['ram_percent'], 1) if latest else None,
        'disk': round(latest['disk_percent'], 1) if latest else None,
        'response_time': round(latest['response_time_ms'], 1) if latest else None,
        'last_seen': format_arabic_datetime(server.get('last_seen_at')),
        'last_seen_html': format_arabic_datetime_html(server.get('last_seen_at'))
    }


@dashboard_bp.route('/dashboard')
@role_required('dashboard')
def index():
    servers = [_server_card(s) for s in ServerModel.list_all()]
    unresolved = AlertModel.count_unresolved()
    recent_alerts = AlertModel.list_filtered(is_resolved=False, limit=8)
    for a in recent_alerts:
        a['created_at_fmt'] = format_arabic_datetime(a['created_at'])
        a['created_at_html'] = format_arabic_datetime_html(a['created_at'])
    return render_template(
        'dashboard.html',
        servers=servers,
        unresolved=unresolved,
        recent_alerts=recent_alerts,
        csrf_token=generate_csrf_token(),
        username=session.get('username'),
        role=session.get('role')
    )


@dashboard_bp.route('/api/dashboard/live')
@role_required('dashboard')
def live_data():
    servers = [_server_card(s) for s in ServerModel.list_all()]
    unresolved = AlertModel.count_unresolved()
    recent_alerts = AlertModel.list_filtered(is_resolved=False, limit=8)
    for a in recent_alerts:
        a['created_at_fmt'] = format_arabic_datetime(a['created_at'])
    return jsonify({
        'servers': servers,
        'unresolved': unresolved,
        'recent_alerts': recent_alerts
    })
