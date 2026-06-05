import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv
from pathlib import Path
from config.env import get_env, get_env_bool, get_env_int

# 自动定位项目根目录下的 .env 文件
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def _resolve_db_url() -> str:
    mode = (get_env("DB_MODE") or "cloud").strip().lower()
    if mode == "local":
        url = get_env("APP_DATABASE_URL_LOCAL")
        if not url:
            raise ValueError("DB_MODE=local 但未在 .env 中找到 APP_DATABASE_URL_LOCAL")
        return url
    url = get_env("APP_DATABASE_URL")
    if not url:
        raise ValueError("DB_MODE=cloud 但未在 .env 中找到 APP_DATABASE_URL")
    return url

DB_URL = _resolve_db_url()
_POOL = None


class _PooledConnection:
    def __init__(self, pool: ThreadedConnectionPool, conn):
        self._pool = pool
        self._conn = conn
        self._closed = False

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            if not self._conn.closed:
                self._conn.rollback()
            self._pool.putconn(self._conn)
        except Exception:
            try:
                self._conn.close()
            except Exception:
                pass


def _get_pool() -> ThreadedConnectionPool | None:
    global _POOL
    if not get_env_bool("DB_POOL_ENABLED", default=True):
        return None
    if _POOL is None:
        minconn = get_env_int("DB_POOL_MINCONN", default=1)
        maxconn = get_env_int("DB_POOL_MAXCONN", default=8)
        _POOL = ThreadedConnectionPool(max(1, minconn), max(maxconn, minconn), DB_URL)
    return _POOL

def get_connection():
    """获取标准的 PostgreSQL 连接（由 DB_MODE 决定使用云端或本地）"""
    pool = _get_pool()
    if pool is None:
        return psycopg2.connect(DB_URL)
    return _PooledConnection(pool, pool.getconn())
