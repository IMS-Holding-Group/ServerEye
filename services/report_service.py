import io
import re
from datetime import timedelta
from xml.sax.saxutils import escape

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import config
from models.alert_model import AlertModel
from models.metric_model import MetricModel
from models.server_model import ServerModel
from utils.datetime_fmt import format_arabic_datetime, now_iso, now_utc


def _register_fonts():
    font_path = config.BASE_DIR / 'static' / 'fonts' / 'IBMPlexSansArabic-Regular.ttf'
    bold_path = config.BASE_DIR / 'static' / 'fonts' / 'IBMPlexSansArabic-Bold.ttf'
    if font_path.exists():
        pdfmetrics.registerFont(TTFont('IBMPlex', str(font_path)))
    if bold_path.exists():
        pdfmetrics.registerFont(TTFont('IBMPlexBold', str(bold_path)))


def _has_arabic(text):
    return bool(re.search(r'[\u0600-\u06FF]', str(text or '')))


def _ar(text):
    """تشكيل العربية وإعادة ترتيب العرض لاتجاه RTL داخل PDF."""
    raw = '' if text is None else str(text)
    if not raw:
        return ''
    if not _has_arabic(raw):
        return raw
    reshaped = arabic_reshaper.reshape(raw)
    return get_display(reshaped)


def _p(text, style):
    return Paragraph(escape(_ar(text)), style)


def _longest_stable_hours(server_id, start_iso, end_iso):
    alerts = AlertModel.list_filtered(server_id=server_id, limit=5000)
    relevant = [
        a for a in alerts
        if start_iso <= a['created_at'] <= end_iso
    ]
    if not relevant:
        from utils.datetime_fmt import parse_iso
        s = parse_iso(start_iso)
        e = parse_iso(end_iso)
        if s and e:
            return max(0.0, (e - s).total_seconds() / 3600.0)
        return 0.0
    times = sorted(a['created_at'] for a in relevant)
    from utils.datetime_fmt import parse_iso
    parsed = [parse_iso(t) for t in times]
    parsed = [p for p in parsed if p]
    if not parsed:
        return 0.0
    start_dt = parse_iso(start_iso) or parsed[0]
    end_dt = parse_iso(end_iso) or now_utc()
    points = [start_dt] + parsed + [end_dt]
    max_gap = 0.0
    for i in range(1, len(points)):
        gap = (points[i] - points[i - 1]).total_seconds() / 3600.0
        if gap > max_gap:
            max_gap = gap
    return max_gap


def build_report_data(period='daily', server_id=None):
    end = now_utc()
    if period == 'weekly':
        start = end - timedelta(days=7)
        period_label = 'أسبوعي'
    else:
        start = end - timedelta(days=1)
        period_label = 'يومي'
    start_iso = start.strftime('%Y-%m-%dT%H:%M:%S')
    end_iso = end.strftime('%Y-%m-%dT%H:%M:%S')

    if server_id:
        servers = [ServerModel.get_by_id(int(server_id))]
        servers = [s for s in servers if s]
    else:
        servers = ServerModel.list_all()

    rows = []
    for server in servers:
        avg = MetricModel.average_in_range(server['id'], start_iso, end_iso)
        sev = AlertModel.count_by_severity_in_range(server['id'], start_iso, end_iso)
        stable = _longest_stable_hours(server['id'], start_iso, end_iso)
        rows.append({
            'server': server,
            'cpu_avg': round(avg['cpu_avg'] or 0, 2) if avg else 0,
            'ram_avg': round(avg['ram_avg'] or 0, 2) if avg else 0,
            'disk_avg': round(avg['disk_avg'] or 0, 2) if avg else 0,
            'rt_avg': round(avg['rt_avg'] or 0, 2) if avg else 0,
            'readings': int(avg['cnt'] or 0) if avg else 0,
            'alerts_critical': sev.get('حرجة', 0),
            'alerts_medium': sev.get('متوسطة', 0),
            'alerts_low': sev.get('منخفضة', 0),
            'stable_hours': round(stable, 2)
        })

    return {
        'period': period,
        'period_label': period_label,
        'start_iso': start_iso,
        'end_iso': end_iso,
        'generated_at': now_iso(),
        'rows': rows
    }


def generate_pdf(report_data):
    _register_fonts()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()
    font_regular = 'IBMPlex' if 'IBMPlex' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    font_bold = 'IBMPlexBold' if 'IBMPlexBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'

    title_style = ParagraphStyle(
        'TitleAR',
        parent=styles['Title'],
        fontName=font_bold,
        fontSize=16,
        leading=22,
        alignment=TA_RIGHT
    )
    normal_style = ParagraphStyle(
        'NormalAR',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=11,
        leading=16,
        alignment=TA_RIGHT
    )
    cell_style = ParagraphStyle(
        'CellAR',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=8,
        leading=11,
        alignment=TA_RIGHT
    )
    header_style = ParagraphStyle(
        'HeaderAR',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=8,
        leading=11,
        textColor=colors.white,
        alignment=TA_RIGHT
    )

    story = []
    story.append(_p('تقرير أداء ServerEye', title_style))
    story.append(Spacer(1, 12))
    story.append(_p(
        f'الفترة: {report_data["period_label"]} | '
        f'من {format_arabic_datetime(report_data["start_iso"])} '
        f'إلى {format_arabic_datetime(report_data["end_iso"])}',
        normal_style
    ))
    story.append(_p(
        f'تاريخ التوليد: {format_arabic_datetime(report_data["generated_at"])}',
        normal_style
    ))
    story.append(Spacer(1, 16))

    headers = [
        'السيرفر',
        'متوسط المعالج %',
        'متوسط الذاكرة %',
        'متوسط التخزين %',
        'متوسط الاستجابة',
        'تنبيهات حرجة',
        'تنبيهات متوسطة',
        'أطول استقرار (ساعة)'
    ]
    table_data = [[_p(h, header_style) for h in headers]]
    for row in report_data['rows']:
        table_data.append([
            _p(row['server']['name'], cell_style),
            _p(str(row['cpu_avg']), cell_style),
            _p(str(row['ram_avg']), cell_style),
            _p(str(row['disk_avg']), cell_style),
            _p(str(row['rt_avg']), cell_style),
            _p(str(row['alerts_critical']), cell_style),
            _p(str(row['alerts_medium']), cell_style),
            _p(str(row['stable_hours']), cell_style)
        ])

    table = Table(table_data, repeatRows=1, colWidths=[70, 55, 55, 55, 55, 50, 55, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.Color(0.93, 0.95, 0.98)])
    ]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer
