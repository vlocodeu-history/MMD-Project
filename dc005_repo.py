# dc005_repo.py — with audit logging like dc001_repo.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from db import connect
from audit import log_on_conn

TABLE  = "dc005_calcs"
ENTITY = "dc005"

def create_dc005_calc(user_id: str, name: str, payload: Dict[str, Any]) -> str:
    clean_name = (name or "DC005").strip() or "DC005"
    with connect() as conn:
        rid = conn.execute(
            text(f"""
                INSERT INTO {TABLE} (user_id, name, data)
                VALUES (:uid, :name, :data)
                RETURNING id::text
            """),
            {"uid": user_id, "name": clean_name, "data": payload},
        ).scalar()

        # AUDIT (include a tiny summary if present)
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
                }},
            )
        except Exception:
            pass

    return str(rid)

def list_dc005_calcs(user_id: str, limit: int = 100) -> List[Tuple[str, str, Any, Any]]:
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

def get_dc005_calc(calc_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        row = conn.execute(
            text(f"SELECT data FROM {TABLE} WHERE id = :id AND user_id = :uid"),
            {"id": calc_id, "uid": user_id},
        ).one_or_none()
    return row[0] if row else None

def update_dc005_calc(
    calc_id: str,
    user_id: str,
    *,
    name: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> bool:
    sets, params = [], {"id": calc_id, "uid": user_id}
    if name is not None:
        params["name"] = (name or "DC005").strip() or "DC005"
        sets.append("name = :name")
    if payload is not None:
        params["data"] = payload
        sets.append("data = :data")
    if not sets:
        return False

    with connect() as conn:
        # Fetch old name to ensure the audit entry always carries a name
        old = conn.execute(
            text(f"SELECT name FROM {TABLE} WHERE id = :id AND user_id = :uid"),
            {"id": calc_id, "uid": user_id},
        ).mappings().one_or_none()
        old_name = old["name"] if old else None

        res = conn.execute(
            text(f"UPDATE {TABLE} SET {', '.join(sets)} WHERE id = :id AND user_id = :uid"),
            params,
        )
        ok = (res.rowcount or 0) > 0

        if ok:
            try:
                nm_for_log = params.get("name", old_name)
                log_on_conn(conn, "UPDATE", ENTITY, entity_id=calc_id, name=nm_for_log)
            except Exception:
                pass

        return ok

def delete_dc005_calc(calc_id: str, user_id: str) -> bool:
    with connect() as conn:
        # Read the name BEFORE deleting so the audit captures the deleted name
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
