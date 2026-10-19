from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from . import config

pool = ConnectionPool(config.DATABASE_URL, min_size=1, max_size=8, kwargs={"row_factory": dict_row}, open=False)

def open_pool():
    pool.open()

@contextmanager
def conn():
    with pool.connection() as c:
        yield c

def one(sql, params=None):
    with conn() as c:
        return c.execute(sql, params).fetchone()

def all_(sql, params=None):
    with conn() as c:
        return c.execute(sql, params).fetchall()

def run(sql, params=None):
    with conn() as c:
        c.execute(sql, params)
