import logging
import statistics
from datetime import timedelta
from pathlib import Path

import config
from models.metric_model import MetricModel
from models.server_model import ServerModel
from utils.datetime_fmt import now_utc, parse_iso

logger = logging.getLogger('servereye.anomaly')

_isolation_models = {}
_last_train_times = {}


def _zscore_check(values, new_value):
    if len(values) < 10:
        return False, 0.0
    try:
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
    except statistics.StatisticsError:
        return False, 0.0
    if stdev == 0:
        return False, 0.0
    z = (new_value - mean) / stdev
    is_anomaly = abs(z) > config.ZSCORE_THRESHOLD
    return is_anomaly, z


def check_baseline_complete(server_id):
    server = ServerModel.get_by_id(server_id)
    if not server or not server.get('is_in_baseline'):
        return False
    count = MetricModel.count_for_server(server_id)
    created = parse_iso(server['created_at'])
    hours_elapsed = 0
    if created:
        hours_elapsed = (now_utc() - created).total_seconds() / 3600.0
    if count >= config.BASELINE_MIN_READINGS or hours_elapsed >= config.BASELINE_MAX_HOURS:
        ServerModel.set_baseline(server_id, False)
        return True
    return False


def evaluate_metric_reading(server_id, cpu, ram, disk, response_time):
    """
    يعيد قاموساً يتضمن:
    - zscore_anomaly: bool
    - isolation_anomaly: bool أو None إن لم يتوفر النموذج
    - severity: منخفضة/متوسطة/حرجة أو None
    - details: نص توضيحي
    """
    check_baseline_complete(server_id)
    server = ServerModel.get_by_id(server_id)
    if not server:
        return None

    recent = MetricModel.get_recent(server_id, config.ZSCORE_WINDOW)
    # استبعاد القراءة الحالية إن كانت قد أُدرجت للتو
    if recent and len(recent) > 0:
        recent = recent[1:] if len(recent) > 1 else []

    metrics_map = {
        'المعالج': (cpu, [r['cpu_percent'] for r in recent]),
        'الذاكرة': (ram, [r['ram_percent'] for r in recent]),
        'التخزين': (disk, [r['disk_percent'] for r in recent]),
        'زمن الاستجابة': (response_time, [r['response_time_ms'] for r in recent])
    }

    z_anomalies = []
    for label, (val, hist) in metrics_map.items():
        is_anom, z = _zscore_check(hist, val)
        if is_anom:
            z_anomalies.append((label, z, val))

    zscore_anomaly = len(z_anomalies) > 0
    isolation_anomaly = predict_isolation(server_id, cpu, ram, disk, response_time)

    if server.get('is_in_baseline'):
        return {
            'zscore_anomaly': zscore_anomaly,
            'isolation_anomaly': isolation_anomaly,
            'severity': None,
            'details': 'السيرفر ضمن فترة التعلّم الأولية؛ لا تُصدر تنبيهات شذوذ.',
            'in_baseline': True,
            'z_anomalies': z_anomalies
        }

    severity = None
    if zscore_anomaly and isolation_anomaly is True:
        severity = 'حرجة'
    elif zscore_anomaly or isolation_anomaly is True:
        severity = 'متوسطة'

    detail_parts = []
    for label, z, val in z_anomalies:
        detail_parts.append(f'{label}={val:.1f} (Z={z:.2f})')
    if isolation_anomaly is True:
        detail_parts.append('نموذج IsolationForest صنّف التركيبة كشاذة')

    return {
        'zscore_anomaly': zscore_anomaly,
        'isolation_anomaly': isolation_anomaly,
        'severity': severity,
        'details': '؛ '.join(detail_parts) if detail_parts else '',
        'in_baseline': False,
        'z_anomalies': z_anomalies
    }


def train_isolation_forest(server_id):
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        logger.error('مكتبة scikit-learn غير متوفرة')
        return False

    rows = MetricModel.get_all_for_server(server_id)
    if len(rows) < 30:
        return False

    data = [
        [r['cpu_percent'], r['ram_percent'], r['disk_percent'], r['response_time_ms']]
        for r in rows
    ]
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42
    )
    model.fit(data)
    _isolation_models[server_id] = model
    _last_train_times[server_id] = now_utc()

    cache_dir = Path(config.BASE_DIR) / 'services' / 'models_cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        import pickle
        with open(cache_dir / f'iforest_{server_id}.pkl', 'wb') as f:
            pickle.dump(model, f)
    except Exception as exc:
        logger.warning('تعذر حفظ نموذج IsolationForest: %s', exc)
    return True


def load_isolation_model(server_id):
    if server_id in _isolation_models:
        return _isolation_models[server_id]
    cache_path = Path(config.BASE_DIR) / 'services' / 'models_cache' / f'iforest_{server_id}.pkl'
    if cache_path.exists():
        try:
            import pickle
            with open(cache_path, 'rb') as f:
                model = pickle.load(f)
            _isolation_models[server_id] = model
            return model
        except Exception:
            return None
    return None


def predict_isolation(server_id, cpu, ram, disk, response_time):
    model = load_isolation_model(server_id)
    if model is None:
        return None
    try:
        pred = model.predict([[cpu, ram, disk, response_time]])
        return bool(pred[0] == -1)
    except Exception as exc:
        logger.warning('فشل تنبؤ IsolationForest: %s', exc)
        return None


def retrain_all_servers():
    servers = ServerModel.list_all()
    for server in servers:
        sid = server['id']
        last = _last_train_times.get(sid)
        if last and (now_utc() - last) < timedelta(hours=config.ISOLATION_RETRAIN_HOURS):
            continue
        try:
            train_isolation_forest(sid)
        except Exception as exc:
            logger.exception('فشل تدريب IsolationForest للسيرفر %s: %s', sid, exc)
