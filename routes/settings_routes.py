from flask import Blueprint, flash, redirect, render_template, request, url_for

from database.db import get_all_settings, set_setting
from utils.security import generate_csrf_token, require_csrf, role_required

settings_bp = Blueprint('settings', __name__)

EDITABLE_KEYS = [
    'cpu_critical',
    'ram_critical',
    'disk_critical',
    'response_time_critical_ms',
    'agent_interval_seconds',
    'email_notify_enabled'
]


@settings_bp.route('/settings', methods=['GET', 'POST'])
@role_required('settings')
def settings_page():
    if request.method == 'POST':
        if not require_csrf():
            return redirect(url_for('settings.settings_page'))
        try:
            cpu = float(request.form.get('cpu_critical', '90'))
            ram = float(request.form.get('ram_critical', '90'))
            disk = float(request.form.get('disk_critical', '90'))
            rt = float(request.form.get('response_time_critical_ms', '2000'))
            interval = int(float(request.form.get('agent_interval_seconds', '60')))
            email_enabled = 'true' if request.form.get('email_notify_enabled') == 'on' else 'false'

            if not (1 <= cpu <= 100 and 1 <= ram <= 100 and 1 <= disk <= 100):
                raise ValueError('عتبات النسب خارج النطاق')
            if rt < 1 or interval < 10:
                raise ValueError('قيم غير صالحة')

            set_setting('cpu_critical', str(cpu))
            set_setting('ram_critical', str(ram))
            set_setting('disk_critical', str(disk))
            set_setting('response_time_critical_ms', str(rt))
            set_setting('agent_interval_seconds', str(interval))
            set_setting('email_notify_enabled', email_enabled)
            flash('تم حفظ الإعدادات. بيانات اتصال البريد تُضبط عبر ملف .env فقط.', 'success')
        except Exception:
            flash('تعذر حفظ الإعدادات. تحقق من القيم المدخلة.', 'error')
        return redirect(url_for('settings.settings_page'))

    settings = get_all_settings()
    return render_template(
        'settings.html',
        settings=settings,
        csrf_token=generate_csrf_token()
    )
