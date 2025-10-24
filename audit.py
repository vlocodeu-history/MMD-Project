# audit.py
from __future__ import annotations
from typing import Any, Optional, Dict
import json
import streamlit as st
from sqlalchemy import text
from db import connect
from auth import current_user

def _actor() -> Dict[str, Optional[str]]:
    u = current_user() or {}
    return {
        "user_id":  u.get("id"),
        "username": u.get("username"),
        "role":     u.get("role"),
    }

def _guess_ip() -> Optional[str]:
    # Streamlit doesn't expose request directly; allow you to stash it in session
    # anywhere you prefer (e.g., from a reverse proxy header on first load).
    # Totally optional — NULL is fine.
    return st.session_state.get("client_ip")

def log_action(
    action: str,                 # 'CREATE' | 'UPDATE' | 'DELETE' | 'LOGIN' | ...
    entity_type: str,            # 'valve_design' | 'dc001' | 'dc002a' | ...
    entity_id: Optional[str] = None,
    name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,  # free-form JSON: inputs, diffs, etc.
    ip_addr: Optional[str] = None,
) -> None:
    act = _actor()
    ip = ip_addr or _guess_ip()
    payload = json.dumps(details) if isinstance(details, dict) else None

    sql = """
        INSERT INTO audit_logs
            (actor_user_id, actor_username, actor_role, action,
             entity_type, entity_id, name, details, ip_addr)
        VALUES
            (:uid, :uname, :urole, :action,
             :etype, :eid, :name, :details::jsonb, :ip::inet)
    """
    with connect() as conn:
        conn.execute(
            text(sql),
            {
                "uid": act["user_id"],
                "uname": act["username"],
                "urole": act["role"],
                "action": action,
                "etype": entity_type,
                "eid": entity_id,
                "name": name,
                "details": payload,
                "ip": ip,
            },
        )

def log_on_conn(conn, action: str, entity: str, *, entity_id: Optional[str] = None,
                name: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
                ip_addr: Optional[str] = None):
    """Write an audit row using an existing transaction (recommended)."""
    u = current_user() or {}
    conn.execute(
        text("""
            INSERT INTO audit_logs (actor_user_id, actor_username, actor_role,
                                    action, entity_type, entity_id, name, details, ip_addr)
            VALUES (:uid, :uname, :role, :action, :etype, :eid, :name, :details, :ip)
        """),
        {
            "uid": u.get("id"),
            "uname": u.get("username"),
            "role": u.get("role"),
            "action": action,
            "etype": entity,
            "eid": entity_id,
            "name": name,
            "details": details or {},
            "ip": ip_addr,
        },
    )

