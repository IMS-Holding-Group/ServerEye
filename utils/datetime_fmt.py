from datetime import datetime, timezone


def now_utc():
    return datetime.now(timezone.utc)


def now_iso():
    return now_utc().strftime('%Y-%m-%dT%H:%M:%S')


def parse_iso(value):
    if not value:
        return None
    text = str(value).replace('Z', '')
    if 'T' in text:
        return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    return datetime.strptime(text[:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)


def format_arabic_datetime(value):
    """صيغة العرض: YYYY/M/Dم H:MMص أو YYYY/M/Dم H:MMم"""
    if value is None:
        return ''
    if isinstance(value, str):
        dt = parse_iso(value)
    else:
        dt = value
    if dt is None:
        return ''
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone()
    hour24 = local.hour
    if hour24 == 0:
        hour12 = 12
        suffix = 'ص'
    elif hour24 < 12:
        hour12 = hour24
        suffix = 'ص'
    elif hour24 == 12:
        hour12 = 12
        suffix = 'م'
    else:
        hour12 = hour24 - 12
        suffix = 'م'
    return f'{local.year}/{local.month}/{local.day}م {hour12}:{local.minute:02d}{suffix}'


def format_arabic_datetime_html(value):
    return format_arabic_datetime(value)
