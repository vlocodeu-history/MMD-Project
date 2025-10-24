# db.py — Streamlit Cloud friendly (psycopg2-binary with pg8000 fallback)
from __future__ import annotations
from contextlib import contextmanager
from typing import Optional, Any
import os
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_engine: Optional[Engine] = None

def _dsn(driver: str = "psycopg2") -> str:
    """Build DSN from st.secrets['postgres'] with a chosen driver."""
    sec = st.secrets["postgres"]  # raises KeyError if not provided
    host = sec["host"]
    port = int(sec.get("port", 5432))
    db   = sec["dbname"]
    user = sec["user"]
    pwd  = sec["password"]
    search_path = sec.get("search_path", "public")
    if driver == "psycopg2":
        # psycopg2 supports sslmode=require and options=-csearch_path=public
        return (
            f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
            f"?sslmode=require&options=-csearch_path%3D{search_path}"
        )
    else:
        # pg8000: ssl=true (uses stdlib context) and options is supported as well
        # (pg8000 ignores 'sslmode', so use ssl=true)
        return (
            f"postgresql+pg8000://{user}:{pwd}@{host}:{port}/{db}"
            f"?ssl=true&options=-csearch_path%3D{search_path}"
        )

def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    # Try psycopg2 first
    try:
        url = _dsn("psycopg2")
        masked = url.replace(st.secrets["postgres"]["password"], "****")
        print("SQLAlchemy URL (masked):", masked)
        _engine = create_engine(url, future=True, pool_pre_ping=True)
        # quick probe to ensure the driver is actually importable
        with _engine.connect() as c:
            c.execute(text("select 1"))
        return _engine
    except Exception as e:
        print("DB check failed (psycopg2 path):", e)

    # Fallback to pg8000 (pure python)
    url = _dsn("pg8000")
    masked = url.replace(st.secrets["postgres"]["password"], "****")
    print("SQLAlchemy URL (masked):", masked)
    _engine = create_engine(url, future=True, pool_pre_ping=True)
    # probe
    with _engine.connect() as c:
        c.execute(text("select 1"))
    return _engine

@contextmanager
def connect():
    eng = get_engine()
    # IMPORTANT: on Streamlit Cloud we do *not* auto-run bootstrap DDL here;
    # schema should be created via Supabase SQL editor / migrations.
    with eng.begin() as conn:
        yield conn

def scalar(conn, sql: str, **params: Any):
    row = conn.execute(text(sql), params).one_or_none()
    return None if row is None else row[0]
