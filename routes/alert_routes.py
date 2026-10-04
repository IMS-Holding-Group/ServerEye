from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from models.alert_model import AlertModel
from models.server_model import ServerModel
from utils.datetime_fmt import format_arabic_datetime, format_arabic_datetime_html
from utils.security import generate_csrf_token, require_csrf, role_required, safe_int

alert_bp = Blueprint('alerts', __name__)


@alert_bp.route('/alerts', methods=['GET', 'POST'])
@role_required('alerts_view')
def alerts_page():
    server_id = request.args.get('server_id')
    severity = (request.args.get('severity') or '').strip() or None
    status = (request.args.get('status') or '').strip()

    sid = safe_int(server_id, None) if server_id not in (None, '') else None
    if server_id not in (None, '') and sid == 0 and server_id != '0':
        sid = None

    is_resolved = None
    if status == 'open':
        is_resolved = False
    elif status == 'resolved':
        is_resolved = True

    alerts = AlertModel.list_filtered(
        server_id=sid if sid else None,
        severity=severity,
        is_resolved=is_resolved,
        limit=300
    )
    for a in alerts:
        a['created_at_fmt'] = format_arabic_datetime(a['created_at'])
        a['created_at_html'] = format_arabic_datetime_html(a['created_at'])
        a['resolved_at_fmt'] = format_arabic_datetime(a.get('resolved_at'))
        a['resolved_at_html'] = format_arabic_datetime_html(a.get('resolved_at'))

    return render_template(
        'alerts.html',
        alerts=alerts,
        servers=ServerModel.list_all(),
        filters={
            'server_id': server_id or '',
            'severity': severity or '',
            'status': status or ''
        },
        csrf_token=generate_csrf_token(),
        can_resolve='alerts_resolve' in __import__('config').ROLE_PERMISSIONS.get(session.get('role'), set())
    )


@alert_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@role_required('alerts_resolve')
def resolve_alert(alert_id):
    if not require_csrf():
        return redirect(url_for('alerts.alerts_page'))
    alert = AlertModel.get_by_id(alert_id)
    if not alert:
        flash('التنبيه غير موجود.', 'error')
        return redirect(url_for('alerts.alerts_page'))
    AlertModel.resolve(alert_id, session.get('user_id'))
    flash('تم تعليم التنبيه كمعالَج.', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True})
    return redirect(request.referrer or url_for('alerts.alerts_page'))


@alert_bp.route('/api/alerts/live')
@role_required('alerts_view')
def alerts_live():
    alerts = AlertModel.list_filtered(is_resolved=False, limit=20)
    for a in alerts:
        a['created_at_fmt'] = format_arabic_datetime(a['created_at'])
    return jsonify({
        'unresolved': AlertModel.count_unresolved(),
        'alerts': alerts
    })
