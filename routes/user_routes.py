import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import config
from models.user_model import UserModel
from utils.datetime_fmt import format_arabic_datetime, format_arabic_datetime_html
from utils.security import generate_csrf_token, require_csrf, role_required, safe_int

user_bp = Blueprint('users', __name__)

USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,32}$')


@user_bp.route('/users', methods=['GET', 'POST', 'DELETE'])
@role_required('users_manage')
def users_page():
    if request.method == 'DELETE' or (request.method == 'POST' and request.form.get('_method') == 'DELETE'):
        if not require_csrf():
            return redirect(url_for('users.users_page'))
        user_id = safe_int(request.form.get('user_id'))
        if user_id == session.get('user_id'):
            flash('لا يمكن حذف حسابك الحالي.', 'error')
        elif user_id:
            UserModel.delete(user_id)
            flash('تم حذف المستخدم.', 'success')
        return redirect(url_for('users.users_page'))

    if request.method == 'POST':
        if not require_csrf():
            return redirect(url_for('users.users_page'))
        action = request.form.get('action') or 'create'
        if action == 'create':
            username = (request.form.get('username') or '').strip()
            password = request.form.get('password') or ''
            role = (request.form.get('role') or '').strip()
            if not USERNAME_RE.match(username):
                flash('اسم المستخدم يجب أن يكون من 3 إلى 32 حرفاً لاتينياً أو أرقاماً أو شرطة سفلية.', 'error')
            elif len(password) < 8:
                flash('كلمة السر يجب ألا تقل عن 8 أحرف.', 'error')
            elif role not in config.ROLES:
                flash('الدور المحدد غير صالح.', 'error')
            elif UserModel.get_by_username(username):
                flash('اسم المستخدم مستخدم مسبقاً.', 'error')
            else:
                try:
                    UserModel.create(username, password, role)
                    flash('تم إنشاء المستخدم بنجاح.', 'success')
                except Exception:
                    flash('تعذر إنشاء المستخدم.', 'error')
        elif action == 'update':
            user_id = safe_int(request.form.get('user_id'))
            username = (request.form.get('username') or '').strip()
            password = request.form.get('password') or ''
            role = (request.form.get('role') or '').strip()
            if not user_id or not USERNAME_RE.match(username) or role not in config.ROLES:
                flash('بيانات التعديل غير صالحة.', 'error')
            else:
                other = UserModel.get_by_username(username)
                if other and other['id'] != user_id:
                    flash('اسم المستخدم مستخدم مسبقاً.', 'error')
                else:
                    UserModel.update(
                        user_id,
                        username=username,
                        password=password if password else None,
                        role=role
                    )
                    flash('تم تحديث المستخدم.', 'success')
        return redirect(url_for('users.users_page'))

    users = UserModel.list_all()
    for u in users:
        u['role_label'] = config.ROLES.get(u['role'], u['role'])
        u['created_at_fmt'] = format_arabic_datetime(u['created_at'])
        u['created_at_html'] = format_arabic_datetime_html(u['created_at'])

    return render_template(
        'users.html',
        users=users,
        roles=config.ROLES,
        csrf_token=generate_csrf_token(),
        current_user_id=session.get('user_id')
    )
