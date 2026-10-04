import functools
import logging
import secrets
import time
from collections import defaultdict

from flask import flash, redirect, request, session, url_for

import config

logger = logging.getLogger('servereye')

_login_attempts = defaultdict(list)


def ensure_csrf_token():
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_hex(32)
        session['csrf_token'] = token
    return token


def generate_csrf_token():
    return ensure_csrf_token()


def validate_csrf():
    form_token = request.form.get('csrf_token', '')
    header_token = request.headers.get('X-CSRF-Token', '')
    session_token = session.get('csrf_token', '')
    submitted = form_token or header_token
    if not session_token or not submitted:
        return False
    try:
        return secrets.compare_digest(session_token, submitted)
    except (TypeError, ValueError):
        return False


def require_csrf():
    if not validate_csrf():
        flash('انتهت صلاحية النموذج. أعد المحاولة.', 'error')
        return False
    return True


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('يجب تسجيل الدخول للمتابعة.', 'error')
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped


def role_required(*permissions):
    def decorator(view):
        @functools.wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            role = session.get('role')
            allowed = config.ROLE_PERMISSIONS.get(role, set())
            if not any(p in allowed for p in permissions):
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة.', 'error')
                return redirect(url_for('dashboard.index'))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def check_login_rate_limit(identifier):
    now = time.time()
    window = config.LOGIN_LOCKOUT_SECONDS
    attempts = [t for t in _login_attempts[identifier] if now - t < window]
    _login_attempts[identifier] = attempts
    if len(attempts) >= config.LOGIN_MAX_ATTEMPTS:
        return False
    return True


def record_failed_login(identifier):
    _login_attempts[identifier].append(time.time())


def clear_failed_logins(identifier):
    _login_attempts.pop(identifier, None)


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp_percent(value):
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if num < 0 or num > 100:
        return None
    return num
