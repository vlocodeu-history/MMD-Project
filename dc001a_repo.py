# dc001a_repo.py — with audit logging like dc001_repo.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from db import connect
from audit import log_on_conn

TABLE = "dc001a_calcs"
ENTITY = "dc001a"

def create_dc001a_calc(user_id: str, name: str, payload: Dict[str, Any]) -> str:
    nm = (name or "DC001A").strip() or "DC001A"
    with connect() as conn:
        new_id = conn.execute(
            text(f"""
                INSERT INTO {TABLE} (user_id, name, data)
                VALUES (:uid, :name, :data)
                RETURNING id::text
            """),
            {"uid": user_id, "name": nm, "data": payload},
        ).scalar()

        # AUDIT (mirror dc001_repo style: include compact base summary when available)
        try:
            base = (payload or {}).get("base", {})
            log_on_conn(
                conn,
                "CREATE",
                ENTITY,
                entity_id=new_id,
                name=nm,
                details={"summary": {
                    "nps_in": base.get("nps_in"),
                    "asme_class": base.get("asme_class"),
                }},
            )
        except Exception:
            pass

        return new_id  # type: ignore[return-value]

def list_dc001a_calcs(user_id: str, limit: int = 200) -> List[Tuple[str, str, Any]]:
    """Return a simple list for picker: [(id, name, created_at), ...]"""
    with connect() as conn:
        rows = conn.execute(
            text(f"""
                SELECT id::text, name, created_at
                FROM {TABLE}
                WHERE user_id = :uid
                ORDER BY updated_at DESC, created_at DESC
                LIMIT :lim
            """),
            {"uid": user_id, "lim": limit},
        ).all()
        out: List[Tuple[str, str, Any]] = []
        for r in rows:
            rid, nm, created = r[0], r[1], r[2] if len(r) > 2 else None
            out.append((rid, nm, created))
        return out

def get_dc001a_calc(calc_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        row = conn.execute(
            text(f"""
                SELECT data
                FROM {TABLE}
                WHERE id = :id AND user_id = :uid
            """),
            {"id": calc_id, "uid": user_id},
        ).one_or_none()
        return row[0] if row else None

def update_dc001a_calc(
    calc_id: str,
    user_id: str,
    *,
    name: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    sets: List[str] = []
    params: Dict[str, Any] = {"id": calc_id, "uid": user_id}

    if name is not None:
        params["name"] = (name or "DC001A").strip() or "DC001A"
        sets.append("name = :name")
    if data is not None:
        params["data"] = data
        sets.append("data = :data")

    if not sets:
        return False

    with connect() as conn:
        # Fetch old to ensure we always have a name to log, and to allow future diffs if needed
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
                # Prefer the new name if provided; otherwise fall back to the previous name
                nm_for_log = params.get("name", old_name)
                log_on_conn(
                    conn,
                    "UPDATE",
                    ENTITY,
                    entity_id=calc_id,
                    name=nm_for_log,
                )
            except Exception:
                pass

        return ok

def delete_dc001a_calc(calc_id: str, user_id: str) -> bool:
    with connect() as conn:
        # Prefetch name BEFORE delete so the audit log contains the deleted name
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
