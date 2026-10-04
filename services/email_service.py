import logging
import smtplib
from email.mime.text import MIMEText

import config

logger = logging.getLogger('servereye.email')


def send_critical_alert_email(server, alert_type, message):
    if not config.SMTP_HOST or not config.SMTP_FROM:
        logger.warning('إعدادات البريد غير مكتملة؛ تم تخطي الإرسال')
        return False

    server_name = server['name'] if server else 'غير معروف'
    subject = f'[ServerEye] تنبيه حرج: {server_name}'
    body = (
        f'تم إنشاء تنبيه بدرجة خطورة حرجة.\n\n'
        f'السيرفر: {server_name}\n'
        f'نوع التنبيه: {alert_type}\n'
        f'التفاصيل: {message}\n'
    )
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = config.SMTP_FROM
    msg['To'] = config.SMTP_USER or config.SMTP_FROM

    try:
        if config.SMTP_USE_TLS:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as smtp:
                smtp.ehlo()
                smtp.starttls()
                if config.SMTP_USER and config.SMTP_PASSWORD:
                    smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as smtp:
                if config.SMTP_USER and config.SMTP_PASSWORD:
                    smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
                smtp.send_message(msg)
        return True
    except Exception as exc:
        logger.exception('فشل إرسال البريد: %s', exc)
        return False
