# db.py  — pg8000 + auto-create database + auto-bootstrap schema
from __future__ import annotations
from contextlib import contextmanager
from typing import Optional, List, Any
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError, OperationalError

_engine: Optional[Engine] = None

# --- Bootstrap DDL in discrete statements (safe to re-run) ---
BOOTSTRAP_DDL: List[str] = [
    # Extension (OK if already installed)
    'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',

    # Users table
    """
    CREATE TABLE IF NOT EXISTS users (
      id           uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      username     text NOT NULL UNIQUE,
      pwd_hash     text NOT NULL,
      salt_hex     text NOT NULL,
      iterations   integer NOT NULL DEFAULT 200000,
      role         text NOT NULL CHECK (role IN ('user','superadmin')),
      first_name   text NOT NULL DEFAULT '',
      last_name    text NOT NULL DEFAULT '',
      created_at   timestamptz NOT NULL DEFAULT now(),
      updated_at   timestamptz NOT NULL DEFAULT now()
    )
    """,

    # Tokens table
    """
    CREATE TABLE IF NOT EXISTS auth_tokens (
      token        text PRIMARY KEY,
      user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      created_at   timestamptz NOT NULL DEFAULT now(),
      exp_at       timestamptz NOT NULL
    )
    """,

    # updated_at trigger fn
    """
    CREATE OR REPLACE FUNCTION set_updated_at()
    RETURNS trigger AS $$
    BEGIN
      NEW.updated_at = now();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql
    """,

    # trigger on users
    "DROP TRIGGER IF EXISTS trg_users_updated_at ON users",
    """
    CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,

    # index on token expiry
    "CREATE INDEX IF NOT EXISTS idx_auth_tokens_exp_at ON auth_tokens(exp_at)",

    # Valve designs
    """
    CREATE TABLE IF NOT EXISTS valve_designs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_valve_designs_updated_at ON valve_designs",
    """
    CREATE TRIGGER trg_valve_designs_updated_at
    BEFORE UPDATE ON valve_designs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_valve_designs_user_created ON valve_designs(user_id, created_at DESC)",

    # DC001 -------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc001_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc001_updated_at ON dc001_calcs",
    """
    CREATE TRIGGER trg_dc001_updated_at
    BEFORE UPDATE ON dc001_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc001_user_created ON dc001_calcs(user_id, created_at DESC)",

    # DC001A ------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc001a_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc001a_updated_at ON dc001a_calcs",
    """
    CREATE TRIGGER trg_dc001a_updated_at
    BEFORE UPDATE ON dc001a_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc001a_user_created ON dc001a_calcs(user_id, created_at DESC)",

    # DC002 -------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc002_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc002_updated_at ON dc002_calcs",
    """
    CREATE TRIGGER trg_dc002_updated_at
    BEFORE UPDATE ON dc002_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc002_user_created ON dc002_calcs(user_id, created_at DESC)",

    # DC002A ------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc002a_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc002a_updated_at ON dc002a_calcs",
    """
    CREATE TRIGGER trg_dc002a_updated_at
    BEFORE UPDATE ON dc002a_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc002a_user_created ON dc002a_calcs(user_id, created_at DESC)",

    # DC003 -------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc003_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc003_updated_at ON dc003_calcs",
    """
    CREATE TRIGGER trg_dc003_updated_at
    BEFORE UPDATE ON dc003_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc003_user_created ON dc003_calcs(user_id, created_at DESC)",

    # DC004 -------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc004_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc004_updated_at ON dc004_calcs",
    """
    CREATE TRIGGER trg_dc004_updated_at
    BEFORE UPDATE ON dc004_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc004_user_created ON dc004_calcs(user_id, created_at DESC)",

    # DC005 -------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc005_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc005_updated_at ON dc005_calcs",
    """
    CREATE TRIGGER trg_dc005_updated_at
    BEFORE UPDATE ON dc005_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc005_user_created ON dc005_calcs(user_id, created_at DESC)",

    # DC005A ------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc005a_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      design_id   uuid NULL REFERENCES valve_designs(id) ON DELETE SET NULL,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc005a_updated_at ON dc005a_calcs",
    """
    CREATE TRIGGER trg_dc005a_updated_at
    BEFORE UPDATE ON dc005a_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc005a_user_created ON dc005a_calcs(user_id, created_at DESC)",

    # DC006 ------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc006_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      design_id   uuid NULL REFERENCES valve_designs(id) ON DELETE SET NULL,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc006_updated_at ON dc006_calcs",
    """
    CREATE TRIGGER trg_dc006_updated_at
    BEFORE UPDATE ON dc006_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc006_user_created ON dc006_calcs(user_id, created_at DESC)",

    # DC006A ------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc006a_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      design_id   uuid NULL REFERENCES valve_designs(id) ON DELETE SET NULL,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc006a_updated_at ON dc006a_calcs",
    """
    CREATE TRIGGER trg_dc006a_updated_at
    BEFORE UPDATE ON dc006a_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc006a_user_created ON dc006a_calcs(user_id, created_at DESC)",

    # DC007-1 (Body) --------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc007_body_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      design_id   uuid NULL REFERENCES valve_designs(id) ON DELETE SET NULL,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc007_body_updated_at ON dc007_body_calcs",
    """
    CREATE TRIGGER trg_dc007_body_updated_at
    BEFORE UPDATE ON dc007_body_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc007_body_user_created ON dc007_body_calcs(user_id, created_at DESC)",

    # DC007-2 (Body Holes) --------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc007_body_holes_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      design_id   uuid NULL REFERENCES valve_designs(id) ON DELETE SET NULL,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc007_body_holes_updated_at ON dc007_body_holes_calcs",
    """
    CREATE TRIGGER trg_dc007_body_holes_updated_at
    BEFORE UPDATE ON dc007_body_holes_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc007_body_holes_user_created ON dc007_body_holes_calcs(user_id, created_at DESC)",

    # DC008 ------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc008_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      design_id   uuid NULL REFERENCES valve_designs(id) ON DELETE SET NULL,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc008_updated_at ON dc008_calcs",
    """
    CREATE TRIGGER trg_dc008_updated_at
    BEFORE UPDATE ON dc008_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc008_user_created ON dc008_calcs(user_id, created_at DESC)",

    # DC010 ------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc010_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      design_id   uuid NULL REFERENCES valve_designs(id) ON DELETE SET NULL,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc010_updated_at ON dc010_calcs",
    """
    CREATE TRIGGER trg_dc010_updated_at
    BEFORE UPDATE ON dc010_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc010_user_created ON dc010_calcs(user_id, created_at DESC)",

    # DC011 ------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc011_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      design_id   uuid NULL REFERENCES valve_designs(id) ON DELETE SET NULL,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc011_updated_at ON dc011_calcs",
    """
    CREATE TRIGGER trg_dc011_updated_at
    BEFORE UPDATE ON dc011_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc011_user_created ON dc011_calcs(user_id, created_at DESC)",

    # DC012 ------------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS dc012_calcs (
      id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      design_id   uuid NULL REFERENCES valve_designs(id) ON DELETE SET NULL,
      name        text NOT NULL,
      data        jsonb NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    "DROP TRIGGER IF EXISTS trg_dc012_updated_at ON dc012_calcs",
    """
    CREATE TRIGGER trg_dc012_updated_at
    BEFORE UPDATE ON dc012_calcs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """,
    "CREATE INDEX IF NOT EXISTS idx_dc012_user_created ON dc012_calcs(user_id, created_at DESC)",
     
     # ---------------- AUDIT LOGS (NEW) ----------------
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
      id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      created_at      timestamptz NOT NULL DEFAULT now(),
      actor_user_id   uuid NULL REFERENCES users(id) ON DELETE SET NULL,
      actor_username  text,
      actor_role      text,
      action          text NOT NULL,               -- CREATE / UPDATE / DELETE / LOGIN / ...
      entity_type     text NOT NULL,               -- e.g., 'valve_design', 'dc002a'
      entity_id       uuid NULL,
      name            text,
      details         jsonb,
      ip_addr         text
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_actor  ON audit_logs(actor_user_id, created_at DESC)",

]

def _build_conn_params():
    sec = st.secrets["postgres"]
    return {
        "host": sec["host"],
        "port": int(sec.get("port", 5432)),
        "db":   sec["dbname"],
        "user": sec["user"],
        "pwd":  sec["password"],
    }

def _dsn(dbname: str) -> str:
    p = _build_conn_params()
    return f"postgresql+pg8000://{p['user']}:{p['pwd']}@{p['host']}:{p['port']}/{dbname}"

def _create_database_if_missing(target_db: str):
    """
    Try connecting to target DB. If it fails because the DB doesn't exist,
    connect to maintenance DB 'postgres' and create it with AUTOCOMMIT.
    """
    try:
        eng_try = create_engine(_dsn(target_db), future=True, pool_pre_ping=True)
        with eng_try.connect():
            return  # success -> DB exists
    except (ProgrammingError, OperationalError) as e:
        msg = str(e)
        # pg8000 error codes often surface in message; be permissive on match
        if "3D000" not in msg and "does not exist" not in msg:
            raise

    maint = create_engine(_dsn("postgres"), future=True, pool_pre_ping=True)
    with maint.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
        c.exec_driver_sql(f'CREATE DATABASE "{target_db}"')

def _run_bootstrap_schema(engine: Engine):
    # Run each statement individually (idempotent / safe to re-run)
    with engine.begin() as conn:
        for stmt in BOOTSTRAP_DDL:
            conn.execute(text(stmt))

def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    params = _build_conn_params()
    target_db = params["db"]

    # 1) ensure DB exists
    _create_database_if_missing(target_db)

    # 2) connect to the target DB
    url = _dsn(target_db)
    masked_url = url.replace(params["pwd"], "****")
    print("SQLAlchemy URL (masked):", masked_url)
    _engine = create_engine(url, future=True, pool_pre_ping=True)

    # 3) ensure schema exists
    _run_bootstrap_schema(_engine)

    return _engine

@contextmanager
def connect():
    eng = get_engine()
    with eng.begin() as conn:
        yield conn

def scalar(conn, sql: str, **params: Any):
    row = conn.execute(text(sql), params).one_or_none()
    return None if row is None else row[0]
#MMDproject2025