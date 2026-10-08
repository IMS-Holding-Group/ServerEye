import sqlite3
from contextlib import contextmanager
from pathlib import Path

import bcrypt

import config
from utils.datetime_fmt import now_iso


def get_connection():
    conn = sqlite3.connect(str(config.DATABASE_PATH), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = Path(config.SCHEMA_PATH).read_text(encoding='utf-8')
    with db_session() as conn:
        conn.executescript(schema_sql)
        _seed_settings(conn)
        _seed_default_users(conn)


def _seed_settings(conn):
    for key, value in config.DEFAULT_THRESHOLDS.items():
        conn.execute(
            'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
            (key, str(value))
        )


def _hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _seed_default_users(conn):
    defaults = [
        ('admin', '', 'admin'),
        ('soc_analyst', '', 'soc_analyst'),
        ('it_manager', '', 'it_manager')
    ]
    created_at = now_iso()
    for username, password, role in defaults:
        existing = conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone()
        if existing:
            continue
        conn.execute(
            'INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)',
            (username, _hash_password(password), role, created_at)
        )


def get_setting(key, default=None):
    with db_session() as conn:
        row = conn.execute(
            'SELECT value FROM settings WHERE key = ?', (key,)
        ).fetchone()
        if row is None:
            return default
        return row['value']


def set_setting(key, value):
    with db_session() as conn:
        conn.execute(
            'INSERT INTO settings (key, value) VALUES (?, ?) '
            'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
            (key, str(value))
        )


def get_all_settings():
    with db_session() as conn:
        rows = conn.execute('SELECT key, value FROM settings ORDER BY key').fetchall()
        return {row['key']: row['value'] for row in rows}
