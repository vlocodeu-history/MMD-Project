# valve_repo.py  — with audit logging aligned to dc001_repo.py improvements
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import json
from sqlalchemy import text
from db import connect
from audit import log_on_conn

# -----------------------
# Internal helpers (diff)
# -----------------------

def _diff_name(old: Optional[str], new: Optional[str]) -> Dict[str, Any]:
    if old == new:
        return {}
    return {"name": {"old": old, "new": new}}

def _diff_top_level(old_data: Dict[str, Any] | None, new_data: Dict[str, Any] | None) -> Dict[str, Any]:
    """Very small diff of top-level keys (inputs/calculated/base); avoids huge payloads."""
    old_data = old_data or {}
    new_data = new_data or {}
    out: Dict[str, Any] = {}
    for k in ("inputs", "calculated", "base"):
        ov = old_data.get(k)
        nv = new_data.get(k)
        if ov != nv:
            out[k] = {"changed": True}
    return out

# -----------------------
# Basic CRUD (per-user)
# -----------------------

def create_valve_design(user_id: str, name: str, payload: Dict[str, Any]) -> str:
    clean_name = (name or "").strip() or "Untitled"
    with connect() as conn:
        new_id = conn.execute(
            text("""
                INSERT INTO valve_designs (user_id, name, data)
                VALUES (:uid, :name, :data)
                RETURNING id::text
            """),
            {"uid": user_id, "name": clean_name, "data": payload},
        ).scalar()

        # AUDIT (same style as dc001, keep a compact summary)
        try:
            log_on_conn(
                conn,
                "CREATE",
                "valve_design",
                entity_id=new_id,
                name=clean_name,
                details={
                    "summary": {
                        "nps_in": payload.get("nps_in"),
                        "asme_class": payload.get("asme_class"),
                    }
                },
            )
        except Exception:
            pass

        return new_id

def list_valve_designs(user_id: str, limit: int = 200):
    with connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id::text, name, created_at, updated_at
                FROM valve_designs
                WHERE user_id = :uid
                ORDER BY updated_at DESC, created_at DESC
                LIMIT :lim
            """),
            {"uid": user_id, "lim": limit},
        ).fetchall()
    return [(r[0], r[1], r[2], r[3]) for r in rows]

def get_valve_design(design_id: str, user_id: str) -> dict | None:
    with connect() as conn:
        r = conn.execute(
            text("""
                SELECT id::text, name, data, created_at, updated_at
                FROM valve_designs
                WHERE id = :id AND user_id = :uid
            """),
            {"id": design_id, "uid": user_id},
        ).mappings().first()
    if not r:
        return None
    out = dict(r["data"] or {})
    out["_meta"] = {
        "id": r["id"],
        "name": r["name"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }
    return out

def update_valve_design(
    design_id: str,
    user_id: str,
    *,
    name: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    sets: List[str] = []
    params: Dict[str, Any] = {"id": design_id, "uid": user_id}

    if name is not None:
        params["name"] = (name or "").strip() or "Untitled"
        sets.append("name = :name")
    if data is not None:
        params["data"] = data
        sets.append("data = :data")
    if not sets:
        return False

    with connect() as conn:
        # Fetch old (for diff + fallback name for logging)
        old = conn.execute(
            text("SELECT name, data FROM valve_designs WHERE id = :id AND user_id = :uid"),
            {"id": design_id, "uid": user_id},
        ).mappings().one_or_none()

        res = conn.execute(
            text(f"UPDATE valve_designs SET {', '.join(sets)} WHERE id = :id AND user_id = :uid"),
            params,
        )
        ok = (res.rowcount or 0) > 0

        if ok:
            try:
                # Build compact diff similar to dc001_repo approach
                old_name = old.get("name") if old else None
                new_name = params.get("name", old_name)
                name_diff = _diff_name(old_name, new_name)

                old_data = old.get("data") if old else None
                new_data = params.get("data") if "data" in params else old_data
                top_level_diff = _diff_top_level(old_data, new_data)

                changes = {}
                changes.update(name_diff)
                if top_level_diff:
                    changes["data"] = top_level_diff

                # Ensure we always log a name (fallback to old if not provided)
                nm_for_log = new_name or old_name

                log_on_conn(
                    conn,
                    "UPDATE",
                    "valve_design",
                    entity_id=design_id,
                    name=nm_for_log,
                    details={"diff": changes} if changes else None,
                )
            except Exception:
                pass

        return ok

def delete_valve_design(design_id: str, user_id: str) -> bool:
    with connect() as conn:
        # Prefetch name BEFORE delete so it appears in the audit log (like dc001_repo)
        try:
            name_before = conn.execute(
                text("SELECT name FROM valve_designs WHERE id = :id AND user_id = :uid"),
                {"id": design_id, "uid": user_id},
            ).scalar()
        except Exception:
            name_before = None

        res = conn.execute(
            text("DELETE FROM valve_designs WHERE id = :id AND user_id = :uid"),
            {"id": design_id, "uid": user_id},
        )
        ok = (res.rowcount or 0) > 0
        if ok:
            try:
                log_on_conn(conn, "DELETE", "valve_design", entity_id=design_id, name=name_before)
            except Exception:
                pass
        return ok

# -----------------------
# Admin helpers
# -----------------------

def list_all_valve_designs(
    *,
    limit: int = 200,
    username_like: Optional[str] = None,
    name_like: Optional[str] = None,
) -> List[Dict[str, Any]]:
    where = ["1=1"]
    params: Dict[str, Any] = {"lim": limit}
    if username_like:
        where.append("u.username ILIKE :uname")
        params["uname"] = f"%{username_like}%"
    if name_like:
        where.append("vd.name ILIKE :nm")
        params["nm"] = f"%{name_like}%"

    sql = f"""
        SELECT
            vd.id::text             AS id,
            u.username              AS username,
            vd.name                 AS name,
            vd.created_at           AS created_at,
            vd.updated_at           AS updated_at,
            (vd.data->>'nps_in')::text              AS nps_in,
            (vd.data->>'asme_class')::text          AS asme_class,
            (vd.data->'calculated'->>'body_wall_thickness_mm')::text AS t_mm,
            (vd.data->'calculated'->>'bore_diameter_mm')::text       AS bore_mm,
            (vd.data->'calculated'->>'face_to_face_mm')::text        AS f2f_mm
        FROM valve_designs vd
        JOIN users u ON u.id = vd.user_id
        WHERE {" AND ".join(where)}
        ORDER BY vd.updated_at DESC, vd.created_at DESC
        LIMIT :lim
    """
    with connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        return [dict(r) for r in rows]

def get_valve_design_with_user(design_id: str) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        row = conn.execute(
            text("""
                SELECT
                    vd.id::text AS id,
                    u.username  AS username,
                    vd.name     AS name,
                    vd.created_at,
                    vd.updated_at,
                    vd.data
                FROM valve_designs vd
                JOIN users u ON u.id = vd.user_id
                WHERE vd.id = :id
            """),
            {"id": design_id},
        ).mappings().one_or_none()
        return dict(row) if row else None
