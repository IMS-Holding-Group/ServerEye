from database.db import db_session
from utils.datetime_fmt import now_iso


class AlertModel:
    @staticmethod
    def create(server_id, alert_type, severity, message):
        with db_session() as conn:
            cur = conn.execute(
                'INSERT INTO alerts (server_id, alert_type, severity, message, '
                'is_resolved, created_at) VALUES (?, ?, ?, ?, 0, ?)',
                (server_id, alert_type, severity, message, now_iso())
            )
            return cur.lastrowid

    @staticmethod
    def get_by_id(alert_id):
        with db_session() as conn:
            row = conn.execute(
                'SELECT a.id, a.server_id, a.alert_type, a.severity, a.message, '
                'a.is_resolved, a.created_at, a.resolved_at, a.resolved_by, s.name AS server_name '
                'FROM alerts a JOIN servers s ON s.id = a.server_id WHERE a.id = ?',
                (alert_id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_filtered(server_id=None, severity=None, is_resolved=None, limit=200):
        query = (
            'SELECT a.id, a.server_id, a.alert_type, a.severity, a.message, '
            'a.is_resolved, a.created_at, a.resolved_at, a.resolved_by, s.name AS server_name '
            'FROM alerts a JOIN servers s ON s.id = a.server_id WHERE 1=1'
        )
        params = []
        if server_id is not None:
            query += ' AND a.server_id = ?'
            params.append(server_id)
        if severity:
            query += ' AND a.severity = ?'
            params.append(severity)
        if is_resolved is not None:
            query += ' AND a.is_resolved = ?'
            params.append(1 if is_resolved else 0)
        query += ' ORDER BY a.created_at DESC LIMIT ?'
        params.append(limit)
        with db_session() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def resolve(alert_id, user_id):
        with db_session() as conn:
            conn.execute(
                'UPDATE alerts SET is_resolved = 1, resolved_at = ?, resolved_by = ? '
                'WHERE id = ? AND is_resolved = 0',
                (now_iso(), user_id, alert_id)
            )
        return True

    @staticmethod
    def count_unresolved():
        with db_session() as conn:
            row = conn.execute(
                'SELECT COUNT(*) AS c FROM alerts WHERE is_resolved = 0'
            ).fetchone()
            return int(row['c']) if row else 0

    @staticmethod
    def count_by_severity_in_range(server_id, start_iso, end_iso):
        with db_session() as conn:
            rows = conn.execute(
                'SELECT severity, COUNT(*) AS c FROM alerts '
                'WHERE server_id = ? AND created_at >= ? AND created_at <= ? '
                'GROUP BY severity',
                (server_id, start_iso, end_iso)
            ).fetchall()
            return {r['severity']: r['c'] for r in rows}

    @staticmethod
    def recent_for_server(server_id, limit=10):
        return AlertModel.list_filtered(server_id=server_id, limit=limit)
