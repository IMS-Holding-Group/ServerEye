import logging

from flask import Blueprint, jsonify, request

from models.metric_model import MetricModel
from models.server_model import ServerModel
from services.alert_service import process_anomaly_result, process_thresholds
from services.anomaly_detection import evaluate_metric_reading
from utils.datetime_fmt import now_iso
from utils.security import clamp_percent

logger = logging.getLogger('servereye.metrics_api')

metrics_bp = Blueprint('metrics_api', __name__)


@metrics_bp.route('/api/metrics', methods=['POST'])
def ingest_metrics():
    try:
        token = request.headers.get('X-Agent-Token', '').strip()
        if not token:
            return jsonify({'ok': False, 'error': 'غير مصرح'}), 401

        server = ServerModel.get_by_token(token)
        if not server:
            return jsonify({'ok': False, 'error': 'غير مصرح'}), 401

        data = request.get_json(silent=True) or {}
        cpu = clamp_percent(data.get('cpu_percent'))
        ram = clamp_percent(data.get('ram_percent'))
        disk = clamp_percent(data.get('disk_percent'))
        try:
            response_time = float(data.get('response_time_ms'))
        except (TypeError, ValueError):
            response_time = None

        if cpu is None or ram is None or disk is None or response_time is None or response_time < 0:
            return jsonify({'ok': False, 'error': 'بيانات غير صالحة'}), 400

        recorded_at = now_iso()
        MetricModel.insert(server['id'], cpu, ram, disk, response_time, recorded_at)
        ServerModel.update_last_seen(server['id'], recorded_at)

        process_thresholds(server['id'], cpu, ram, disk, response_time)
        result = evaluate_metric_reading(server['id'], cpu, ram, disk, response_time)
        process_anomaly_result(server['id'], result)

        return jsonify({'ok': True}), 200
    except Exception as exc:
        logger.exception('فشل استقبال القراءات: %s', exc)
        return jsonify({'ok': False, 'error': 'خطأ داخلي'}), 500
