# dc005a_repo.py — with audit logging like dc001_repo.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from db import connect
from audit import log_on_conn

TABLE  = "dc005a_calcs"
ENTITY = "dc005a"

# -------------------------------------------------------------------
# Create
# -------------------------------------------------------------------
def create_dc005a_calc(
    user_id: str,
    name: str,
    payload: Dict[str, Any],
    design_id: Optional[str] = None,
) -> str:
    """
    Insert a DC005A calculation. `payload` is a Python dict (JSONB).
    If `design_id` is provided, the row is linked to a valve design.
    Returns the new row id (as text/uuid).
    """
    clean_name = (name or "DC005A").strip() or "DC005A"
    sql = f"""
        INSERT INTO {TABLE} (user_id, design_id, name, data)
        VALUES (:uid, :design_id, :name, :data)
        RETURNING id::text
    """
    with connect() as conn:
        rid = conn.execute(
            text(sql),
            {
                "uid": user_id,
                "design_id": design_id,
                "name": clean_name,
                "data": payload,   # SQLAlchemy binds JSON correctly
            },
        ).scalar()

        # AUDIT: include a tiny summary if available (keeps logs compact)
        try:
            base = (payload or {}).get("base", {})
            log_on_conn(
                conn,
                "CREATE",
                ENTITY,
                entity_id=rid,
                name=clean_name,
                details={"summary": {
                    "nps_in": base.get("nps_in"),
                    "asme_class": base.get("asme_class"),
                    "design_id": design_id,
                }},
            )
        except Exception:
            pass

        return rid  # already text


# -------------------------------------------------------------------
# Read (user-scoped)
# -------------------------------------------------------------------
def list_dc005a_calcs(user_id: str, limit: int = 200):
    with connect() as conn:
        rows = conn.execute(
            text(f"""
                SELECT id::text, name, created_at, updated_at
                FROM {TABLE}
                WHERE user_id = :uid
                ORDER BY updated_at DESC, created_at DESC
                LIMIT :lim
            """),
            {"uid": user_id, "lim": int(limit)},
        ).fetchall()
    return [(r[0], r[1], r[2], r[3]) for r in rows]


def get_dc005a_calc(calc_id: str, user_id: str) -> dict | None:
    with connect() as conn:
        r = conn.execute(
            text(f"""
                SELECT id::text, name, data, created_at, updated_at, design_id::text AS design_id
                FROM {TABLE}
                WHERE id = :id AND user_id = :uid
            """),
            {"id": calc_id, "uid": user_id},
        ).mappings().first()
    if not r:
        return None
    out = dict(r["data"] or {})
    out["_meta"] = {
        "id": r["id"],
        "name": r["name"],
        "design_id": r["design_id"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }
    return out


# -------------------------------------------------------------------
# Update / Delete (user-scoped)
# -------------------------------------------------------------------
def update_dc005a_calc(
    calc_id: str,
    user_id: str,
    *,
    name: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    sets: List[str] = []
    params: Dict[str, Any] = {"id": calc_id, "uid": user_id}

    if name is not None:
        params["name"] = (name or "DC005A").strip() or "DC005A"
        sets.append("name = :name")
    if data is not None:
        params["data"] = data
        sets.append("data = :data")

    if not sets:
        return False

    sql = f"""
        UPDATE {TABLE}
        SET {", ".join(sets)}
        WHERE id = :id AND user_id = :uid
    """
    with connect() as conn:
        # Fetch old name so audit always carries a value
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


def delete_dc005a_calc(calc_id: str, user_id: str) -> bool:
    sql_del = f"DELETE FROM {TABLE} WHERE id = :id AND user_id = :uid"
    with connect() as conn:
        # Read the name BEFORE deleting so the audit captures it
        try:
            name_before = conn.execute(
                text(f"SELECT name FROM {TABLE} WHERE id = :id AND user_id = :uid"),
                {"id": calc_id, "uid": user_id},
            ).scalar()
        except Exception:
            name_before = None

        res = conn.execute(text(sql_del), {"id": calc_id, "uid": user_id})
        ok = (res.rowcount or 0) > 0

        if ok:
            try:
                log_on_conn(conn, "DELETE", ENTITY, entity_id=calc_id, name=name_before)
            except Exception:
                pass

        return ok
