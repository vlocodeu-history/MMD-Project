# db.py — simple connector (no bootstrap; Supabase)
from __future__ import annotations
from contextlib import contextmanager
from typing import Optional, Any
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_engine: Optional[Engine] = None

def _dsn() -> str:
    sec = st.secrets["postgres"]
    host = sec["host"]
    port = int(sec.get("port", 5432))
    db   = sec["dbname"]
    user = sec["user"]
    pwd  = sec["password"]
    # db.py _dsn()
    return (
      f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
      f"?sslmode=require&options=-csearch_path%3Dpublic"
    )


def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine
    url = _dsn()
    masked_url = url.replace(st.secrets["postgres"]["password"], "****")
    print("SQLAlchemy URL (masked):", masked_url)
    _engine = create_engine(url, future=True, pool_pre_ping=True)
    return _engine

@contextmanager
def connect():
    eng = get_engine()
    with eng.begin() as conn:
        yield conn

def scalar(conn, sql: str, **params: Any):
    row = conn.execute(text(sql), params).one_or_none()
    return None if row is None else row[0]
