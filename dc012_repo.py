# dc012_repo.py — with audit logging
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from db import connect
from audit import log_on_conn

TABLE  = "dc012_calcs"
ENTITY = "dc012"

# -------------------------------------------------------------------
# Create
# -------------------------------------------------------------------
def create_dc012_calc(
    user_id: str,
    name: str,
    payload: Dict[str, Any],
    design_id: Optional[str] = None,
) -> str:
    """
    Insert a DC012 calculation. `payload` is a Python dict (JSONB).
    If `design_id` is provided, this row is linked to a valve design.
    Returns the new row id (uuid::text).
    """
    clean_name = (name or "DC012").strip() or "DC012"
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
                "data": payload,   # SQLAlchemy binds JSON/JSONB correctly
            },
        ).scalar()

        # AUDIT (compact summary from base)
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
                    "valve_weight_kg": base.get("valve_weight_kg"),
                    "valve_design_id": base.get("valve_design_id") or design_id,
                }},
            )
        except Exception:
            pass

        return rid  # type: ignore[return-value]

# -------------------------------------------------------------------
# Read (user-scoped)
# -------------------------------------------------------------------
def list_dc012_calcs(user_id: str, limit: int = 200):
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

def get_dc012_calc(calc_id: str, user_id: str) -> dict | None:
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
def update_dc012_calc(
    calc_id: str,
    user_id: str,
    *,
    name: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    sets: List[str] = []
    params: Dict[str, Any] = {"id": calc_id, "uid": user_id}
    if name is not None:
        params["name"] = (name or "DC012").strip() or "DC012"
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
        # grab old name for meaningful audit
        old = conn.execute(
            text(f"SELECT name FROM {TABLE} WHERE id = :id AND user_id = :uid"),
            {"id": calc_id, "uid": user_id},
        ).mappings().one_or_none()
        old_name = old["name"] if old else None

        res = conn.execute(text(sql), params)
        ok = (res.rowcount or 0) > 0

        if ok:
            try:
                name_for_log = params.get("name", old_name)
                log_on_conn(conn, "UPDATE", ENTITY, entity_id=calc_id, name=name_for_log)
            except Exception:
                pass

        return ok

def delete_dc012_calc(calc_id: str, user_id: str) -> bool:
    sql = f"DELETE FROM {TABLE} WHERE id = :id AND user_id = :uid"
    with connect() as conn:
        # fetch name before deletion so the log includes it
        try:
            name_before = conn.execute(
                text(f"SELECT name FROM {TABLE} WHERE id = :id AND user_id = :uid"),
                {"id": calc_id, "uid": user_id},
            ).scalar()
        except Exception:
            name_before = None

        res = conn.execute(text(sql), {"id": calc_id, "uid": user_id})
        ok = (res.rowcount or 0) > 0

        if ok:
            try:
                log_on_conn(conn, "DELETE", ENTITY, entity_id=calc_id, name=name_before)
            except Exception:
                pass

        return ok

# -------------------------------------------------------------------
# Admin helpers (no user filter)
# -------------------------------------------------------------------
def admin_delete_dc012_calc(calc_id: str) -> bool:
    sql = f"DELETE FROM {TABLE} WHERE id = :id"
    with connect() as conn:
        # fetch name before admin delete
        try:
            name_before = conn.execute(
                text(f"SELECT name FROM {TABLE} WHERE id = :id"),
                {"id": calc_id},
            ).scalar()
        except Exception:
            name_before = None

        res = conn.execute(text(sql), {"id": calc_id})
        ok = (res.rowcount or 0) > 0

        if ok:
            try:
                log_on_conn(conn, "DELETE", ENTITY, entity_id=calc_id, name=name_before)
            except Exception:
                pass

        return ok

def get_dc012_calc_with_user(calc_id: str):
    """
    Return one DC012 row + owner username, name, timestamps, data, design_id.
    """
    sql = f"""
        SELECT
          d.id::text AS id,
          d.name,
          d.design_id::text AS design_id,
          d.created_at,
          d.updated_at,
          u.id::text AS user_id,
          u.username,
          d.data
        FROM {TABLE} d
        JOIN users u ON u.id = d.user_id
        WHERE d.id = :id
    """
    with connect() as conn:
        row = conn.execute(text(sql), {"id": calc_id}).mappings().one_or_none()
        return dict(row) if row else None

def list_all_dc012_calcs(
    *,
    limit: int = 500,
    username_like: Optional[str] = None,
    name_like: Optional[str] = None,
    design_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Admin listing across all users with JSON summary columns extracted.
    """
    where = ["1=1"]
    params: Dict[str, Any] = {"lim": int(limit)}

    if username_like:
        where.append("u.username ILIKE :uname")
        params["uname"] = f"%{username_like}%"

    if name_like:
        where.append("d.name ILIKE :dname")
        params["dname"] = f"%{name_like}%"

    if design_id:
        where.append("d.design_id = :design_id")
        params["design_id"] = design_id

    sql = f"""
        SELECT
          d.id::text         AS id,
          d.name             AS name,
          d.design_id::text  AS design_id,
          d.created_at       AS created_at,
          d.updated_at       AS updated_at,
          u.id::text         AS user_id,
          u.username         AS username,

          -- base
          (d.data->'base'->>'valve_design_id')::text    AS valve_design_id,
          (d.data->'base'->>'valve_design_name')::text  AS valve_design_name,
          (d.data->'base'->>'nps_in')::text             AS nps_in,
          (d.data->'base'->>'asme_class')::text         AS asme_class,
          (d.data->'base'->>'bore_diameter_mm')::text   AS bore_mm,
          (d.data->'base'->>'operating_pressure_mpa')::text AS Po_MPa,
          (d.data->'base'->>'valve_weight_kg')::text    AS valve_weight_kg,

          -- inputs
          (d.data->'inputs'->>'P_kg')::text             AS P_kg,
          (d.data->'inputs'->>'thread')::text           AS thread,
          (d.data->'inputs'->>'A_mm2')::text            AS A_mm2,
          (d.data->'inputs'->>'N')::text                AS N,
          (d.data->'inputs'->>'angle')::text            AS angle,
          (d.data->'inputs'->>'F_rated_kg')::text       AS F_rated_kg,

          -- computed
          (d.data->'computed'->>'per_bolt_kg')::text    AS per_bolt_kg,
          (d.data->'computed'->>'Ec_ok')::text          AS Ec_ok,
          (d.data->'computed'->>'Es_MPa')::text         AS Es_MPa,
          (d.data->'computed'->>'material')::text       AS material,
          (d.data->'computed'->>'allowable_MPa')::text  AS allowable_MPa,
          (d.data->'computed'->>'stress_ok')::text      AS stress_ok

        FROM {TABLE} d
        JOIN users u ON u.id = d.user_id
        WHERE {" AND ".join(where)}
        ORDER BY d.updated_at DESC, d.created_at DESC
        LIMIT :lim
    """
    with connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        return [dict(r) for r in rows]
