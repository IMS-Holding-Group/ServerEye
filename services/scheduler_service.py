import logging
import threading
import time

from services.alert_service import check_agent_timeouts
from services.anomaly_detection import retrain_all_servers

logger = logging.getLogger('servereye.scheduler')

_started = False
_stop_event = threading.Event()


def _loop():
    last_retrain = 0
    while not _stop_event.is_set():
        try:
            check_agent_timeouts()
        except Exception as exc:
            logger.exception('خطأ في فحص مهلة الوكلاء: %s', exc)
        now = time.time()
        if now - last_retrain >= 3600:
            try:
                retrain_all_servers()
                last_retrain = now
            except Exception as exc:
                logger.exception('خطأ في إعادة تدريب النماذج: %s', exc)
        _stop_event.wait(60)


def start_scheduler():
    global _started
    if _started:
        return
    _started = True
    thread = threading.Thread(target=_loop, name='servereye-scheduler', daemon=True)
    thread.start()
    logger.info('تم تشغيل خدمة الجدولة')
