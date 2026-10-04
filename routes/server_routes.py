from datetime import timedelta

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from models.alert_model import AlertModel
from models.metric_model import MetricModel
from models.server_model import ServerModel
from services.alert_service import derive_server_status
from utils.datetime_fmt import format_arabic_datetime, format_arabic_datetime_html, now_utc
from utils.security import generate_csrf_token, require_csrf, role_required

server_bp = Blueprint('servers', __name__)


@server_bp.route('/servers', methods=['GET', 'POST'])
@role_required('servers_view', 'servers_manage')
def servers_list():
    new_token = None
    if request.method == 'POST':
        if session.get('role') != 'admin':
            flash('ليس لديك صلاحية لإضافة سيرفرات.', 'error')
            return redirect(url_for('servers.servers_list'))
        if not require_csrf():
            return redirect(url_for('servers.servers_list'))
        name = (request.form.get('name') or '').strip()
        os_type = (request.form.get('os_type') or '').strip()
        host_address = (request.form.get('host_address') or '').strip()
        description = (request.form.get('description') or '').strip()
        if not name or os_type not in ('Linux', 'Windows Server') or not host_address:
            flash('يرجى تعبئة الحقول المطلوبة بشكل صحيح.', 'error')
        else:
            try:
                _, token = ServerModel.create(name, os_type, host_address, description)
                new_token = token
                flash('تم إضافة السيرفر بنجاح. انسخ مفتاح الوكيل الآن؛ لن يُعرض لاحقاً.', 'success')
            except Exception:
                flash('تعذر إضافة السيرفر. تحقق من البيانات وحاول مجدداً.', 'error')

    servers = ServerModel.list_all()
    items = []
    for s in servers:
        latest = MetricModel.get_latest(s['id'])
        items.append({
            **s,
            'status': derive_server_status(s['id'], latest),
            'created_at_fmt': format_arabic_datetime(s['created_at']),
            'created_at_html': format_arabic_datetime_html(s['created_at']),
            'last_seen_fmt': format_arabic_datetime(s.get('last_seen_at')),
            'last_seen_html': format_arabic_datetime_html(s.get('last_seen_at'))
        })
    return render_template(
        'servers.html',
        servers=items,
        new_token=new_token,
        csrf_token=generate_csrf_token(),
        can_manage=session.get('role') == 'admin'
    )


@server_bp.route('/servers/<int:server_id>', methods=['GET', 'POST', 'DELETE'])
@role_required('servers_view', 'servers_manage')
def server_detail(server_id):
    server = ServerModel.get_by_id(server_id)
    if not server:
        flash('السيرفر غير موجود.', 'error')
        return redirect(url_for('servers.servers_list'))

    if request.method == 'DELETE' or (request.method == 'POST' and request.form.get('_method') == 'DELETE'):
        if session.get('role') != 'admin':
            flash('ليس لديك صلاحية لحذف السيرفرات.', 'error')
            return redirect(url_for('servers.servers_list'))
        if not require_csrf():
            return redirect(url_for('servers.servers_list'))
        ServerModel.delete(server_id)
        flash('تم حذف السيرفر وكل البيانات المرتبطة به.', 'success')
        return redirect(url_for('servers.servers_list'))

    if request.method == 'POST':
        if session.get('role') != 'admin':
            flash('ليس لديك صلاحية لتعديل السيرفرات.', 'error')
            return redirect(url_for('servers.server_detail', server_id=server_id))
        if not require_csrf():
            return redirect(url_for('servers.server_detail', server_id=server_id))
        name = (request.form.get('name') or '').strip()
        os_type = (request.form.get('os_type') or '').strip()
        host_address = (request.form.get('host_address') or '').strip()
        description = (request.form.get('description') or '').strip()
        if not name or os_type not in ('Linux', 'Windows Server') or not host_address:
            flash('يرجى تعبئة الحقول المطلوبة بشكل صحيح.', 'error')
        else:
            ServerModel.update(server_id, name, os_type, host_address, description)
            flash('تم تحديث بيانات السيرفر.', 'success')
            return redirect(url_for('servers.server_detail', server_id=server_id))
        server = ServerModel.get_by_id(server_id)

    latest = MetricModel.get_latest(server_id)
    alerts = AlertModel.recent_for_server(server_id, 15)
    for a in alerts:
        a['created_at_fmt'] = format_arabic_datetime(a['created_at'])
        a['created_at_html'] = format_arabic_datetime_html(a['created_at'])

    return render_template(
        'server_details.html',
        server=server,
        status=derive_server_status(server_id, latest),
        latest=latest,
        alerts=alerts,
        csrf_token=generate_csrf_token(),
        can_manage=session.get('role') == 'admin',
        created_at_html=format_arabic_datetime_html(server['created_at']),
        last_seen_html=format_arabic_datetime_html(server.get('last_seen_at'))
    )


@server_bp.route('/api/servers/<int:server_id>/metrics')
@role_required('servers_view')
def server_metrics_api(server_id):
    server = ServerModel.get_by_id(server_id)
    if not server:
        return jsonify({'error': 'غير موجود'}), 404
    range_key = (request.args.get('range') or 'hour').strip()
    now = now_utc()
    if range_key == 'week':
        start = now - timedelta(days=7)
    elif range_key == 'day':
        start = now - timedelta(days=1)
    else:
        start = now - timedelta(hours=1)
        range_key = 'hour'
    start_iso = start.strftime('%Y-%m-%dT%H:%M:%S')
    rows = MetricModel.get_range(server_id, start_iso)
    return jsonify({
        'range': range_key,
        'points': [
            {
                't': r['recorded_at'],
                't_fmt': format_arabic_datetime(r['recorded_at']),
                'cpu': r['cpu_percent'],
                'ram': r['ram_percent'],
                'disk': r['disk_percent'],
                'rt': r['response_time_ms']
            }
            for r in rows
        ]
    })
