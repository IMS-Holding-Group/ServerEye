import secrets

from database.db import db_session
from utils.datetime_fmt import now_iso


class ServerModel:
    @staticmethod
    def list_all():
        with db_session() as conn:
            rows = conn.execute(
                'SELECT id, name, os_type, host_address, agent_token, description, '
                'created_at, is_in_baseline, last_seen_at FROM servers ORDER BY name'
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(server_id):
        with db_session() as conn:
            row = conn.execute(
                'SELECT id, name, os_type, host_address, agent_token, description, '
                'created_at, is_in_baseline, last_seen_at FROM servers WHERE id = ?',
                (server_id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_token(token):
        with db_session() as conn:
            row = conn.execute(
                'SELECT id, name, os_type, host_address, agent_token, description, '
                'created_at, is_in_baseline, last_seen_at FROM servers WHERE agent_token = ?',
                (token,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(name, os_type, host_address, description=''):
        token = secrets.token_urlsafe(32)
        with db_session() as conn:
            cur = conn.execute(
                'INSERT INTO servers (name, os_type, host_address, agent_token, description, '
                'created_at, is_in_baseline) VALUES (?, ?, ?, ?, ?, ?, 1)',
                (name, os_type, host_address, token, description or '', now_iso())
            )
            return cur.lastrowid, token

    @staticmethod
    def update(server_id, name, os_type, host_address, description=''):
        with db_session() as conn:
            conn.execute(
                'UPDATE servers SET name = ?, os_type = ?, host_address = ?, description = ? '
                'WHERE id = ?',
                (name, os_type, host_address, description or '', server_id)
            )
        return True

    @staticmethod
    def delete(server_id):
        with db_session() as conn:
            conn.execute('DELETE FROM metrics WHERE server_id = ?', (server_id,))
            conn.execute('DELETE FROM alerts WHERE server_id = ?', (server_id,))
            conn.execute('DELETE FROM servers WHERE id = ?', (server_id,))
        return True

    @staticmethod
    def set_baseline(server_id, is_in_baseline):
        with db_session() as conn:
            conn.execute(
                'UPDATE servers SET is_in_baseline = ? WHERE id = ?',
                (1 if is_in_baseline else 0, server_id)
            )

    @staticmethod
    def update_last_seen(server_id, timestamp=None):
        ts = timestamp or now_iso()
        with db_session() as conn:
            conn.execute(
                'UPDATE servers SET last_seen_at = ? WHERE id = ?',
                (ts, server_id)
            )
