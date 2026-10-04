import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', '')
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY غير معرّف في ملف .env')

FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
DATABASE_PATH = BASE_DIR / 'database' / 'servereye.db'
SCHEMA_PATH = BASE_DIR / 'database' / 'schema.sql'

SESSION_LIFETIME_MINUTES = 60
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300

DEFAULT_THRESHOLDS = {
    'cpu_critical': '90',
    'ram_critical': '90',
    'disk_critical': '90',
    'response_time_critical_ms': '2000',
    'agent_interval_seconds': '60',
    'email_notify_enabled': os.getenv('EMAIL_NOTIFY_ENABLED', 'false')
}

SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587') or '587')
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', '')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() in ('1', 'true', 'yes')

BASELINE_MIN_READINGS = 50
BASELINE_MAX_HOURS = 24
ZSCORE_WINDOW = 100
ZSCORE_THRESHOLD = 3.0
ISOLATION_RETRAIN_HOURS = 24

ROLES = {
    'admin': 'مسؤول النظام',
    'soc_analyst': 'محلل مركز العمليات الأمنية',
    'it_manager': 'مدير تقنية المعلومات'
}

ROLE_PERMISSIONS = {
    'admin': {
        'dashboard', 'servers_view', 'servers_manage', 'alerts_view',
        'alerts_resolve', 'reports', 'users_manage', 'settings'
    },
    'soc_analyst': {
        'dashboard', 'servers_view', 'alerts_view', 'alerts_resolve', 'reports'
    },
    'it_manager': {
        'dashboard', 'servers_view', 'alerts_view', 'reports'
    }
}
