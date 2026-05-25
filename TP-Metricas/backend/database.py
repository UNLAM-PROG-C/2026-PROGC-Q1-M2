import threading
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from contextlib import contextmanager
from config import (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
                    DB_MIN_CONNECTIONS, DB_MAX_CONNECTIONS)

# Thread-safe connection pool (OS-level thread synchronization via psycopg2's ThreadedConnectionPool)
_pool: pool.ThreadedConnectionPool = None
_pool_lock = threading.Lock()


def init_pool():
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = pool.ThreadedConnectionPool(
                minconn=DB_MIN_CONNECTIONS,
                maxconn=DB_MAX_CONNECTIONS,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                options="-c client_encoding=UTF8"
            )


def get_pool() -> pool.ThreadedConnectionPool:
    if _pool is None:
        init_pool()
    return _pool


@contextmanager
def get_connection():
    """Context manager that yields a raw DB connection from the pool."""
    p = get_pool()
    conn = p.getconn()
    try:
        yield conn
    finally:
        p.putconn(conn)


@contextmanager
def get_cursor(commit: bool = True):
    """Context manager that yields (cursor, conn). Auto-commits or rolls back."""
    p = get_pool()
    conn = p.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur, conn
            if commit:
                conn.commit()
            else:
                conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def close_pool():
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
