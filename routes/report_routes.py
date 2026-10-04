from flask import Blueprint, render_template, request, send_file, session

from models.server_model import ServerModel
from services.report_service import build_report_data, generate_pdf
from utils.datetime_fmt import format_arabic_datetime, format_arabic_datetime_html
from utils.security import generate_csrf_token, role_required, safe_int

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports', methods=['GET'])
@role_required('reports')
def reports_page():
    period = (request.args.get('period') or 'daily').strip()
    if period not in ('daily', 'weekly'):
        period = 'daily'
    server_id = request.args.get('server_id') or ''
    sid = safe_int(server_id, None) if server_id else None
    if sid == 0 and server_id != '0':
        sid = None

    report = build_report_data(period=period, server_id=sid if sid else None)
    for row in report['rows']:
        pass
    report['start_fmt'] = format_arabic_datetime(report['start_iso'])
    report['end_fmt'] = format_arabic_datetime(report['end_iso'])
    report['generated_fmt'] = format_arabic_datetime(report['generated_at'])
    report['start_html'] = format_arabic_datetime_html(report['start_iso'])
    report['end_html'] = format_arabic_datetime_html(report['end_iso'])
    report['generated_html'] = format_arabic_datetime_html(report['generated_at'])

    return render_template(
        'reports.html',
        report=report,
        servers=ServerModel.list_all(),
        period=period,
        server_id=server_id,
        csrf_token=generate_csrf_token(),
        username=session.get('username')
    )


@report_bp.route('/reports/export', methods=['GET'])
@report_bp.route('/reports/<string:period>/export', methods=['GET'])
@role_required('reports')
def export_report(period=None):
    period = (period or request.args.get('period') or 'daily').strip()
    if period not in ('daily', 'weekly'):
        period = 'daily'
    server_id = request.args.get('server_id') or ''
    sid = safe_int(server_id, None) if server_id else None
    if sid == 0 and server_id != '0':
        sid = None
    report = build_report_data(period=period, server_id=sid if sid else None)
    pdf_buffer = generate_pdf(report)
    filename = f'servereye_report_{period}.pdf'
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
