# dc002_repo.py — with audit logging like dc001_repo.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from db import connect
from audit import log_on_conn

TABLE = "dc002_calcs"
ENTITY = "dc002"

# Create
def create_dc002_calc(user_id: str, name: str, data: Dict[str, Any]) -> str:
    nm = (name or "DC002").strip() or "DC002"
    sql = text(f"""
        INSERT INTO {TABLE} (user_id, name, data)
        VALUES (:uid, :name, CAST(:data AS JSONB))
        RETURNING id::text
    """)
    with connect() as conn:
        rid = conn.execute(sql, {"uid": user_id, "name": nm, "data": data}).scalar()

        # AUDIT (include compact base summary when available)
        try:
            base = (data or {}).get("base", {})
            log_on_conn(
                conn,
                "CREATE",
                ENTITY,
                entity_id=rid,
                name=nm,
                details={"summary": {
                    "nps_in":     base.get("nps_in"),
                    "asme_class": base.get("asme_class"),
                }},
            )
        except Exception:
            pass

    return str(rid)

# List (by user) - return neat ISO-8601 (UTC) timestamps as text
def list_dc002_calcs(user_id: str, limit: int = 500) -> List[Tuple[str, str, str, str]]:
    sql = text(f"""
        SELECT
            id::text,
            name,
            -- Format as UTC ISO-8601 (no millis) for clean display
            to_char((created_at AT TIME ZONE 'UTC'), 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS created_at,
            to_char((updated_at AT TIME ZONE 'UTC'), 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS updated_at
        FROM {TABLE}
        WHERE user_id = :uid
        ORDER BY updated_at DESC, created_at DESC
        LIMIT :lim
    """)
    with connect() as conn:
        rows = conn.execute(sql, {"uid": user_id, "lim": int(limit)}).fetchall()
    return [(r[0], r[1], r[2], r[3]) for r in rows]

# Get one (enforce ownership) - now returns data merged with meta
def get_dc002_calc(calc_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    sql = text(f"""
        SELECT
            id::text AS id,
            name,
            data,
            to_char((created_at AT TIME ZONE 'UTC'), 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS created_at,
            to_char((updated_at AT TIME ZONE 'UTC'), 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS updated_at
        FROM {TABLE}
        WHERE id = :id AND user_id = :uid
    """)
    with connect() as conn:
        row = conn.execute(sql, {"id": calc_id, "uid": user_id}).mappings().first()
    if not row:
        return None
    data = row.get("data") or {}
    out: Dict[str, Any] = {}
    out.update(data if isinstance(data, dict) else {})
    out["id"] = row.get("id")
    out["name"] = row.get("name")
    out["created_at"] = row.get("created_at")
    out["updated_at"] = row.get("updated_at")
    return out

# Get with envelope (name/timestamps) if needed (kept for completeness)
def get_dc002_calc_with_meta(calc_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    sql = text(f"""
        SELECT
            id::text AS id,
            name,
            data,
            to_char((created_at AT TIME ZONE 'UTC'), 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS created_at,
            to_char((updated_at AT TIME ZONE 'UTC'), 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS updated_at
        FROM {TABLE}
        WHERE id = :id AND user_id = :uid
    """)
    with connect() as conn:
        r = conn.execute(sql, {"id": calc_id, "uid": user_id}).mappings().first()
    return dict(r) if r else None

# Update (name and/or data) — with audit log
def update_dc002_calc(
    calc_id: str,
    user_id: str,
    *,
    name: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    if name is None and data is None:
        return False

    sets, params = [], {"id": calc_id, "uid": user_id}
    if name is not None:
        params["name"] = (name or "DC002").strip() or "DC002"
        sets.append("name = :name")
    if data is not None:
        params["data"] = data
        sets.append("data = CAST(:data AS JSONB)")

    sql = text(f"UPDATE {TABLE} SET {', '.join(sets)} WHERE id = :id AND user_id = :uid")
    with connect() as conn:
        # fetch old for safe logging (so we always have a name)
        old = conn.execute(
            text(f"SELECT name FROM {TABLE} WHERE id = :id AND user_id = :uid"),
            {"id": calc_id, "uid": user_id},
        ).mappings().one_or_none()
        old_name = old["name"] if old else None

        res = conn.execute(sql, params)
        ok = (res.rowcount or 0) > 0

        if ok:
            try:
                nm_for_log = params.get("name", old_name)
                log_on_conn(conn, "UPDATE", ENTITY, entity_id=calc_id, name=nm_for_log)
            except Exception:
                pass

    return ok

# Delete — with audit log that includes deleted name
def delete_dc002_calc(calc_id: str, user_id: str) -> bool:
    with connect() as conn:
        # prefetch name BEFORE delete so the audit shows the deleted name
        try:
            name_before = conn.execute(
                text(f"SELECT name FROM {TABLE} WHERE id = :id AND user_id = :uid"),
                {"id": calc_id, "uid": user_id},
            ).scalar()
        except Exception:
            name_before = None

        res = conn.execute(
            text(f"DELETE FROM {TABLE} WHERE id = :id AND user_id = :uid"),
            {"id": calc_id, "uid": user_id},
        )
        ok = (res.rowcount or 0) > 0

        if ok:
            try:
                log_on_conn(conn, "DELETE", ENTITY, entity_id=calc_id, name=name_before)
            except Exception:
                pass

    return ok

# (Optional) Admin list all
def list_dc002_all(limit: int = 500) -> List[Dict[str, Any]]:
    sql = text(f"""
        SELECT
            c.id::text,
            c.user_id::text,
            u.username,
            c.name,
            to_char((c.created_at AT TIME ZONE 'UTC'), 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS created_at,
            to_char((c.updated_at AT TIME ZONE 'UTC'), 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS updated_at
        FROM {TABLE} c
        JOIN users u ON u.id = c.user_id
        ORDER BY c.updated_at DESC, c.created_at DESC
        LIMIT :lim
    """)
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, {"lim": int(limit)}).mappings().all()]
