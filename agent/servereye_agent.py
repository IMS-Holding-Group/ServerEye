#!/usr/bin/env python3
"""وكيل ServerEye الخفيف لجمع مقاييس الأداء وإرسالها للخادم المركزي."""

import json
import logging
import socket
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:
    print('المكتبة psutil غير مثبتة. نفّذ: pip install psutil')
    sys.exit(1)

try:
    from urllib import request as urlrequest
    from urllib.error import URLError, HTTPError
except ImportError:
    import urllib2 as urlrequest
    from urllib2 import URLError, HTTPError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger('servereye_agent')

CONFIG_PATH = Path(__file__).resolve().parent / 'agent_config.json'


def load_config():
    if not CONFIG_PATH.exists():
        example = Path(__file__).resolve().parent / 'agent_config.example.json'
        logger.error(
            'ملف الإعداد غير موجود: %s — انسخ %s إلى agent_config.json وعدّل القيم.',
            CONFIG_PATH, example
        )
        sys.exit(1)
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    required = ['server_url', 'agent_token', 'interval_seconds']
    for key in required:
        if key not in cfg:
            logger.error('المفتاح المطلوب ناقص في الإعداد: %s', key)
            sys.exit(1)
    return cfg


def measure_response_time(host='127.0.0.1', port=None, timeout=2.0):
    """قياس زمن استجابة بسيط لخدمة محلية عبر TCP أو زمن فتح مقبس محلي."""
    target_port = port or 22
    start = time.perf_counter()
    try:
        sock = socket.create_connection((host, target_port), timeout=timeout)
        sock.close()
        return (time.perf_counter() - start) * 1000.0
    except OSError:
        # محاولة بديلة: قياس زمن إنشاء مقبس محلي
        start2 = time.perf_counter()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.close()
        except OSError:
            pass
        return (time.perf_counter() - start2) * 1000.0 + 999.0


def collect_metrics(cfg):
    cpu = float(psutil.cpu_percent(interval=1))
    ram = float(psutil.virtual_memory().percent)
    disk_path = cfg.get('disk_path') or ('C:\\' if sys.platform.startswith('win') else '/')
    disk = float(psutil.disk_usage(disk_path).percent)
    probe_host = cfg.get('probe_host', '127.0.0.1')
    probe_port = cfg.get('probe_port')
    response_time = measure_response_time(probe_host, probe_port)
    return {
        'cpu_percent': round(cpu, 2),
        'ram_percent': round(ram, 2),
        'disk_percent': round(disk, 2),
        'response_time_ms': round(response_time, 2)
    }


def send_metrics(cfg, payload):
    url = cfg['server_url'].rstrip('/') + '/api/metrics'
    body = json.dumps(payload).encode('utf-8')
    req = urlrequest.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-Agent-Token', cfg['agent_token'])
    with urlrequest.urlopen(req, timeout=15) as resp:
        return resp.getcode(), resp.read().decode('utf-8', errors='replace')


def main():
    cfg = load_config()
    interval = max(10, int(cfg.get('interval_seconds', 60)))
    logger.info('بدء وكيل ServerEye. الفاصل الزمني: %s ثانية', interval)
    while True:
        try:
            metrics = collect_metrics(cfg)
            code, body = send_metrics(cfg, metrics)
            if 200 <= code < 300:
                logger.info('أُرسلت القراءات بنجاح: %s', metrics)
            else:
                logger.warning('استجابة غير متوقعة (%s): %s', code, body)
        except HTTPError as exc:
            logger.warning('فشل الإرسال (HTTP %s). إعادة المحاولة لاحقاً.', exc.code)
        except URLError as exc:
            logger.warning('تعذر الاتصال بالخادم: %s. إعادة المحاولة لاحقاً.', exc.reason)
        except Exception as exc:
            logger.warning('خطأ أثناء الجمع أو الإرسال: %s', exc)
        time.sleep(interval)


if __name__ == '__main__':
    main()
