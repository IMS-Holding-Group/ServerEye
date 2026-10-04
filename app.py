import logging
from datetime import timedelta

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException

import config
from database.db import init_database
from routes.alert_routes import alert_bp
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.metrics_api import metrics_bp
from routes.report_routes import report_bp
from routes.server_routes import server_bp
from routes.settings_routes import settings_bp
from routes.user_routes import user_bp
from services.scheduler_service import start_scheduler
from utils.security import ensure_csrf_token

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger('servereye')


def create_app():
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=config.SESSION_LIFETIME_MINUTES)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False

    @app.after_request
    def harden_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Server'] = 'ServerEye'
        response.headers.pop('X-Powered-By', None)
        return response

    @app.context_processor
    def inject_globals():
        return {
            'csrf_token': ensure_csrf_token() if session.get('user_id') or request.endpoint == 'auth.login' else session.get('csrf_token', ''),
            'current_username': session.get('username'),
            'current_role': session.get('role'),
            'role_labels': config.ROLES,
            'permissions': config.ROLE_PERMISSIONS.get(session.get('role'), set())
        }

    @app.route('/')
    def home():
        if session.get('user_id'):
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    @app.errorhandler(400)
    def err_400(e):
        return 'طلب غير صالح', 400

    @app.errorhandler(403)
    def err_403(e):
        return 'غير مصرح بالوصول', 403

    @app.errorhandler(404)
    def err_404(e):
        return 'الصفحة غير موجودة', 404

    @app.errorhandler(Exception)
    def err_generic(e):
        if isinstance(e, HTTPException):
            return e
        logger.exception('خطأ غير متوقع')
        return 'حدث خطأ غير متوقع', 500

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(server_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(settings_bp)

    init_database()
    start_scheduler()
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=config.FLASK_DEBUG, use_reloader=False)
