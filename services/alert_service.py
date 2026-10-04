import logging

from database.db import get_setting
from models.alert_model import AlertModel
from models.server_model import ServerModel
from services.email_service import send_critical_alert_email
from utils.datetime_fmt import now_utc, parse_iso

logger = logging.getLogger('servereye.alerts')


def create_alert(server_id, alert_type, severity, message, notify=True):
    alert_id = AlertModel.create(server_id, alert_type, severity, message)
    if notify and severity == 'حرجة':
        try:
            enabled = get_setting('email_notify_enabled', 'false')
            if str(enabled).lower() in ('1', 'true', 'yes'):
                server = ServerModel.get_by_id(server_id)
                send_critical_alert_email(server, alert_type, message)
        except Exception as exc:
            logger.exception('فشل إرسال بريد التنبيه: %s', exc)
    return alert_id


def process_thresholds(server_id, cpu, ram, disk, response_time):
    alerts = []
    try:
        cpu_th = float(get_setting('cpu_critical', '90'))
        ram_th = float(get_setting('ram_critical', '90'))
        disk_th = float(get_setting('disk_critical', '90'))
        rt_th = float(get_setting('response_time_critical_ms', '2000'))
    except ValueError:
        cpu_th, ram_th, disk_th, rt_th = 90.0, 90.0, 90.0, 2000.0

    checks = [
        (cpu >= cpu_th, 'عتبة المعالج', f'استخدام المعالج بلغ {cpu:.1f}% وتجاوز العتبة {cpu_th}%'),
        (ram >= ram_th, 'عتبة الذاكرة', f'استخدام الذاكرة بلغ {ram:.1f}% وتجاوز العتبة {ram_th}%'),
        (disk >= disk_th, 'عتبة التخزين', f'امتلاء التخزين بلغ {disk:.1f}% وتجاوز العتبة {disk_th}%'),
        (response_time >= rt_th, 'عتبة زمن الاستجابة', f'زمن الاستجابة بلغ {response_time:.0f} مللي ثانية وتجاوز العتبة {rt_th:.0f}')
    ]
    for triggered, alert_type, message in checks:
        if triggered:
            aid = create_alert(server_id, alert_type, 'حرجة', message)
            alerts.append(aid)
    return alerts


def process_anomaly_result(server_id, result):
    if not result or result.get('in_baseline'):
        return None
    severity = result.get('severity')
    if not severity:
        return None
    details = result.get('details') or 'تم اكتشاف نمط شاذ في المقاييس'
    return create_alert(server_id, 'شذوذ ذكي', severity, details)


def check_agent_timeouts():
    try:
        interval = int(float(get_setting('agent_interval_seconds', '60')))
    except ValueError:
        interval = 60
    timeout_seconds = interval * 3
    now = now_utc()
    created = []
    for server in ServerModel.list_all():
        last_seen = parse_iso(server.get('last_seen_at'))
        if last_seen is None:
            created_at = parse_iso(server.get('created_at'))
            if created_at and (now - created_at).total_seconds() > timeout_seconds:
                open_alerts = AlertModel.list_filtered(
                    server_id=server['id'],
                    is_resolved=False,
                    limit=20
                )
                if any(a['alert_type'] == 'فقدان اتصال الوكيل' for a in open_alerts):
                    continue
                aid = create_alert(
                    server['id'],
                    'فقدان اتصال الوكيل',
                    'حرجة',
                    f'لم تُستلم قراءات من الوكيل لأكثر من {timeout_seconds} ثانية.'
                )
                created.append(aid)
            continue
        elapsed = (now - last_seen).total_seconds()
        if elapsed > timeout_seconds:
            open_alerts = AlertModel.list_filtered(
                server_id=server['id'],
                is_resolved=False,
                limit=20
            )
            if any(a['alert_type'] == 'فقدان اتصال الوكيل' for a in open_alerts):
                continue
            aid = create_alert(
                server['id'],
                'فقدان اتصال الوكيل',
                'حرجة',
                f'آخر اتصال كان منذ {int(elapsed)} ثانية (الحد الأقصى {timeout_seconds}).'
            )
            created.append(aid)
    return created


def derive_server_status(server_id, latest_metric=None):
    open_alerts = AlertModel.list_filtered(server_id=server_id, is_resolved=False, limit=50)
    if any(a['severity'] == 'حرجة' for a in open_alerts):
        return 'حرج'
    if any(a['severity'] == 'متوسطة' for a in open_alerts):
        return 'تحذير'
    if latest_metric:
        try:
            cpu_th = float(get_setting('cpu_critical', '90'))
            ram_th = float(get_setting('ram_critical', '90'))
            disk_th = float(get_setting('disk_critical', '90'))
        except ValueError:
            cpu_th, ram_th, disk_th = 90.0, 90.0, 90.0
        warn_cpu = cpu_th * 0.8
        warn_ram = ram_th * 0.8
        warn_disk = disk_th * 0.8
        if (
            latest_metric['cpu_percent'] >= warn_cpu
            or latest_metric['ram_percent'] >= warn_ram
            or latest_metric['disk_percent'] >= warn_disk
        ):
            return 'تحذير'
    return 'طبيعي'
