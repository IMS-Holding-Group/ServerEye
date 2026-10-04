import bcrypt

from database.db import db_session
from utils.datetime_fmt import now_iso


class UserModel:
    @staticmethod
    def get_by_id(user_id):
        with db_session() as conn:
            row = conn.execute(
                'SELECT id, username, password_hash, role, created_at FROM users WHERE id = ?',
                (user_id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_username(username):
        with db_session() as conn:
            row = conn.execute(
                'SELECT id, username, password_hash, role, created_at FROM users WHERE username = ?',
                (username,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_all():
        with db_session() as conn:
            rows = conn.execute(
                'SELECT id, username, role, created_at FROM users ORDER BY id'
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def create(username, password, role):
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')
        with db_session() as conn:
            cur = conn.execute(
                'INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)',
                (username, password_hash, role, now_iso())
            )
            return cur.lastrowid

    @staticmethod
    def update(user_id, username=None, password=None, role=None):
        user = UserModel.get_by_id(user_id)
        if not user:
            return False
        new_username = username if username else user['username']
        new_role = role if role else user['role']
        new_hash = user['password_hash']
        if password:
            new_hash = bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt()
            ).decode('utf-8')
        with db_session() as conn:
            conn.execute(
                'UPDATE users SET username = ?, password_hash = ?, role = ? WHERE id = ?',
                (new_username, new_hash, new_role, user_id)
            )
        return True

    @staticmethod
    def delete(user_id):
        with db_session() as conn:
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        return True

    @staticmethod
    def verify_password(password_hash, password):
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
