from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.user_model import UserModel
from utils.security import (
    check_login_rate_limit,
    clear_failed_logins,
    ensure_csrf_token,
    record_failed_login,
    require_csrf
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))

    error = None
    if request.method == 'POST':
        if not require_csrf():
            return redirect(url_for('auth.login'))
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        client_ip = request.remote_addr or 'unknown'
        rate_key = f'{client_ip}:{username}'

        if not check_login_rate_limit(rate_key):
            error = 'تم تجاوز عدد محاولات الدخول. حاول لاحقاً.'
            return render_template('login.html', error=error, csrf_token=ensure_csrf_token())

        user = UserModel.get_by_username(username)
        if not user or not UserModel.verify_password(user['password_hash'], password):
            record_failed_login(rate_key)
            error = 'اسم المستخدم أو كلمة السر غير صحيحة.'
            return render_template('login.html', error=error, csrf_token=ensure_csrf_token())

        clear_failed_logins(rate_key)
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session.permanent = True
        ensure_csrf_token()
        flash('تم تسجيل الدخول بنجاح.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('login.html', error=error, csrf_token=ensure_csrf_token())


@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    flash('تم تسجيل الخروج.', 'success')
    return redirect(url_for('auth.login'))
