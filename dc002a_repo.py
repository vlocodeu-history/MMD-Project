# dc002a_repo.py — with audit logging like dc001_repo.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from db import connect
from audit import log_on_conn

TABLE = "dc002a_calcs"
ENTITY = "dc002a"

# Create
def create_dc002a_calc(user_id: str, name: str, data: Dict[str, Any]) -> str:
    nm = (name or "DC002A").strip() or "DC002A"
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

# List (by user) -> [(id, name, created_at, updated_at)]
def list_dc002a_calcs(user_id: str, limit: int = 500) -> List[Tuple[str, str, str, str]]:
    sql = text(f"""
        SELECT id::text, name, created_at::text, updated_at::text
        FROM {TABLE}
        WHERE user_id = :uid
        ORDER BY updated_at DESC, created_at DESC
        LIMIT :lim
    """)
    with connect() as conn:
        rows = conn.execute(sql, {"uid": user_id, "lim": int(limit)}).fetchall()
    return [(r[0], r[1], r[2], r[3]) for r in rows]

# Get one (ownership enforced)
def get_dc002a_calc(calc_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    sql = text(f"""
        SELECT data
        FROM {TABLE}
        WHERE id = :id AND user_id = :uid
    """)
    with connect() as conn:
        row = conn.execute(sql, {"id": calc_id, "uid": user_id}).scalar()
    return row if isinstance(row, dict) else None

# Get with envelope (name + timestamps)
def get_dc002a_calc_with_meta(calc_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    sql = text(f"""
        SELECT id::text AS id, name, data, created_at::text AS created_at, updated_at::text AS updated_at
        FROM {TABLE}
        WHERE id = :id AND user_id = :uid
    """)
    with connect() as conn:
        r = conn.execute(sql, {"id": calc_id, "uid": user_id}).mappings().first()
    return dict(r) if r else None

# Update (name and/or data) — with audit log
def update_dc002a_calc(
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
        params["name"] = (name or "DC002A").strip() or "DC002A"
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
def delete_dc002a_calc(calc_id: str, user_id: str) -> bool:
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
