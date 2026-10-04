from database.db import db_session
from utils.datetime_fmt import now_iso


class MetricModel:
    @staticmethod
    def insert(server_id, cpu_percent, ram_percent, disk_percent, response_time_ms, recorded_at=None):
        ts = recorded_at or now_iso()
        with db_session() as conn:
            cur = conn.execute(
                'INSERT INTO metrics (server_id, cpu_percent, ram_percent, disk_percent, '
                'response_time_ms, recorded_at) VALUES (?, ?, ?, ?, ?, ?)',
                (server_id, cpu_percent, ram_percent, disk_percent, response_time_ms, ts)
            )
            return cur.lastrowid

    @staticmethod
    def get_latest(server_id):
        with db_session() as conn:
            row = conn.execute(
                'SELECT id, server_id, cpu_percent, ram_percent, disk_percent, '
                'response_time_ms, recorded_at FROM metrics WHERE server_id = ? '
                'ORDER BY recorded_at DESC LIMIT 1',
                (server_id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_recent(server_id, limit=100):
        with db_session() as conn:
            rows = conn.execute(
                'SELECT id, server_id, cpu_percent, ram_percent, disk_percent, '
                'response_time_ms, recorded_at FROM metrics WHERE server_id = ? '
                'ORDER BY recorded_at DESC LIMIT ?',
                (server_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_range(server_id, start_iso, end_iso=None):
        with db_session() as conn:
            if end_iso:
                rows = conn.execute(
                    'SELECT id, server_id, cpu_percent, ram_percent, disk_percent, '
                    'response_time_ms, recorded_at FROM metrics '
                    'WHERE server_id = ? AND recorded_at >= ? AND recorded_at <= ? '
                    'ORDER BY recorded_at ASC',
                    (server_id, start_iso, end_iso)
                ).fetchall()
            else:
                rows = conn.execute(
                    'SELECT id, server_id, cpu_percent, ram_percent, disk_percent, '
                    'response_time_ms, recorded_at FROM metrics '
                    'WHERE server_id = ? AND recorded_at >= ? ORDER BY recorded_at ASC',
                    (server_id, start_iso)
                ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def count_for_server(server_id):
        with db_session() as conn:
            row = conn.execute(
                'SELECT COUNT(*) AS c FROM metrics WHERE server_id = ?',
                (server_id,)
            ).fetchone()
            return int(row['c']) if row else 0

    @staticmethod
    def get_all_for_server(server_id):
        with db_session() as conn:
            rows = conn.execute(
                'SELECT cpu_percent, ram_percent, disk_percent, response_time_ms, recorded_at '
                'FROM metrics WHERE server_id = ? ORDER BY recorded_at ASC',
                (server_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def average_in_range(server_id, start_iso, end_iso):
        with db_session() as conn:
            row = conn.execute(
                'SELECT AVG(cpu_percent) AS cpu_avg, AVG(ram_percent) AS ram_avg, '
                'AVG(disk_percent) AS disk_avg, AVG(response_time_ms) AS rt_avg, '
                'COUNT(*) AS cnt FROM metrics '
                'WHERE server_id = ? AND recorded_at >= ? AND recorded_at <= ?',
                (server_id, start_iso, end_iso)
            ).fetchone()
            return dict(row) if row else None
