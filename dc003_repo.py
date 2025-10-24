# dc003_repo.py — with audit logging like dc001_repo.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from db import connect
from audit import log_on_conn

TABLE = "dc003_calcs"
ENTITY = "dc003"

# Create
def create_dc003_calc(user_id: str, name: str, payload: Dict[str, Any]) -> str:
    clean_name = (name or "DC003").strip() or "DC003"
    sql = f"""
        INSERT INTO {TABLE} (user_id, name, data)
        VALUES (:uid, :name, :data)
        RETURNING id::text
    """
    with connect() as conn:
        rid = conn.execute(
            text(sql),
            {"uid": user_id, "name": clean_name, "data": payload},
        ).scalar()

        # AUDIT: include compact base summary if available
        try:
            base = (payload or {}).get("base", {})
            log_on_conn(
                conn,
                "CREATE",
                ENTITY,
                entity_id=rid,
                name=clean_name,
                details={
                    "summary": {
                        "nps_in": base.get("nps_in"),
                        "asme_class": base.get("asme_class"),
                    }
                },
            )
        except Exception:
            pass

    return str(rid)

# List (user-scoped)
def list_dc003_calcs(user_id: str, limit: int = 50) -> List[Tuple[str, str, Any, Any]]:
    sql = f"""
        SELECT id::text, name, created_at, updated_at
        FROM {TABLE}
        WHERE user_id = :uid
        ORDER BY updated_at DESC, created_at DESC
        LIMIT :lim
    """
    with connect() as conn:
        rows = conn.execute(text(sql), {"uid": user_id, "lim": int(limit)}).fetchall()
    return [(r[0], r[1], r[2], r[3]) for r in rows]

# Get one (user-scoped)
def get_dc003_calc(calc_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    sql = f"""
        SELECT data
        FROM {TABLE}
        WHERE id = :id AND user_id = :uid
    """
    with connect() as conn:
        row = conn.execute(text(sql), {"id": calc_id, "uid": user_id}).one_or_none()
    return row[0] if row else None

# Update (user-scoped) + audit
def update_dc003_calc(
    calc_id: str,
    user_id: str,
    *,
    name: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> bool:
    sets, params = [], {"id": calc_id, "uid": user_id}
    if name is not None:
        params["name"] = (name or "DC003").strip() or "DC003"
        sets.append("name = :name")
    if payload is not None:
        params["data"] = payload
        sets.append("data = :data")
    if not sets:
        return False

    sql = f"UPDATE {TABLE} SET {', '.join(sets)} WHERE id = :id AND user_id = :uid"
    with connect() as conn:
        # fetch old name for robust logging
        old = conn.execute(
            text(f"SELECT name FROM {TABLE} WHERE id = :id AND user_id = :uid"),
            {"id": calc_id, "uid": user_id},
        ).mappings().one_or_none()
        old_name = old["name"] if old else None

        res = conn.execute(text(sql), params)
        ok = (res.rowcount or 0) > 0

        if ok:
            try:
                nm_for_log = params.get("name", old_name)
                log_on_conn(conn, "UPDATE", ENTITY, entity_id=calc_id, name=nm_for_log)
            except Exception:
                pass

        return ok

# Delete (user-scoped) + audit with deleted name
def delete_dc003_calc(calc_id: str, user_id: str) -> bool:
    with connect() as conn:
        # prefetch name BEFORE delete so audit shows the deleted name
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
