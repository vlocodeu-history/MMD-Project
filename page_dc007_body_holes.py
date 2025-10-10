# page_dc007_body_holes.py
import os
from PIL import Image
import streamlit as st

def _img_dc007_2(size_px: int = 360):
    for p in ["dc007_body_holes.png", "assets/dc007_body_holes.png", "static/dc007_body_holes.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Fig. 2 ASME B16.34 – hole locations/notations", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load DC007-2 diagram ({e}).")
            return
    st.info("Add **dc007_body_holes.png** (or put it in ./assets/ or ./static/) to show the figure here.")

def render_dc007_body_holes():
    """
    DC007 Sheet 2 of 2 (Body) — Holes requirements (ASME B16.34 §6.1.1, Table 3A & Table VI-1)

    Uses t_m from DC007-1 (preferred: t_m + C/A shown as 15.7 mm in your sheet).
    If not present, falls back to 15.7 mm.
    Checks:
      f'   >= 0.25 * t_m
      f'+g' >= 1.00 * t_m
      e°   >= 0.25 * t_m
    """
    st.markdown("<h2 style='text-align:center;margin:0;'>Body Wall Thickness Calc. in acc. With ASME B16.34</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC 007 Sheet 2 of 2 (Holes requirements)</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Header (carry over)
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        st.text_input("Class rating — ASME", value=str(st.session_state.get("valve_asme_class", 600)), disabled=True)
    with col2:
        st.text_input("Design pressure Pa [MPa]", value=str(st.session_state.get("operating_pressure_mpa", 10.21)), disabled=True)
    with col3:
        st.text_input("Design temperature T [°C]", value="-29 / +150", disabled=True)
    with col4:
        st.text_input("Corrosion allowance C/A [mm]", value="3", disabled=True)

    st.markdown("### DRILLED AND TAPPED HOLES")

    # Pull t_m from DC007-1 if available (prefer the +C/A number used on your sheet: 15.7 mm)
    tm_from_body = None
    if isinstance(st.session_state.get("dc007_body"), dict):
        # if you want to use plain t_m instead, switch key to "t_m_mm"
        tm_from_body = st.session_state["dc007_body"].get("t_m_plus_CA_mm") or st.session_state["dc007_body"].get("t_m_mm")

    t_m = float(tm_from_body) if tm_from_body is not None else 15.7  # your sheet shows 15.7 mm

    # show the reference t_m
    st.text_input("min wall thickness  tₘ  [mm]", value=f"{t_m:.1f} mm", disabled=True,
                  help="From ASME B16.34 Table 3A / Table VI-1 (typically tₘ + C/A for holes check).")

    # Inputs: actual minimum measurements (green cells in sheet)
    i1, i2, i3 = st.columns([1.1, 1.1, 1.1])
    with i1:
        f_min = st.number_input("minimum thickness  f'  [mm]", value=14.1, step=0.1, format="%.1f")
    with i2:
        fg_min = st.number_input("minimum thickness  f' + g'  [mm]", value=27.8, step=0.1, format="%.1f")
    with i3:
        e_min = st.number_input("minimum thickness  e°  [mm]", value=20.7, step=0.1, format="%.1f")

    # Required limits from §6.1.1
    req_f  = 0.25 * t_m
    req_fg = 1.00 * t_m
    req_e  = 0.25 * t_m

    # Results / checks
    c1, c2, c3 = st.columns([1.1, 1.1, 1.1])
    with c1:
        ok_f = f_min >= req_f
        st.text_input("Requirement  f'  ≥ 0.25 · tₘ  → limit [mm]", value=f"{req_f:.2f}", disabled=True)
        st.markdown(f"<div style='margin-top:.25rem;font-weight:700;color:{'#16a34a' if ok_f else '#dc2626'}'>{'OK' if ok_f else 'NOT OK'}</div>", unsafe_allow_html=True)
    with c2:
        ok_fg = fg_min >= req_fg
        st.text_input("Requirement  f'+g' ≥ tₘ  → limit [mm]", value=f"{req_fg:.2f}", disabled=True)
        st.markdown(f"<div style='margin-top:.25rem;font-weight:700;color:{'#16a34a' if ok_fg else '#dc2626'}'>{'OK' if ok_fg else 'NOT OK'}</div>", unsafe_allow_html=True)
    with c3:
        ok_e = e_min >= req_e
        st.text_input("Requirement  e°  ≥ 0.25 · tₘ  → limit [mm]", value=f"{req_e:.2f}", disabled=True)
        st.markdown(f"<div style='margin-top:.25rem;font-weight:700;color:{'#16a34a' if ok_e else '#dc2626'}'>{'OK' if ok_e else 'NOT OK'}</div>", unsafe_allow_html=True)

    # Overall verdict
    overall = ok_f and ok_fg and ok_e
    st.markdown(
        f"<div style='margin-top:.75rem;padding:.35rem .8rem;display:inline-block;border-radius:.4rem;"
        f"background:{'#22c55e' if overall else '#ef4444'};color:#fff;font-weight:700;'>"
        f"{'ALL REQUIREMENTS MET' if overall else 'REQUIREMENTS NOT MET'}</div>",
        unsafe_allow_html=True
    )

    _img_dc007_2(360)

    # Persist for any downstream use
    st.session_state["dc007_body_holes"] = {
        "t_m_mm": t_m,
        "f_min_mm": float(f_min),
        "fg_min_mm": float(fg_min),
        "e_min_mm": float(e_min),
        "req_f_mm": req_f,
        "req_fg_mm": req_fg,
        "req_e_mm": req_e,
        "ok_f": ok_f, "ok_fg": ok_fg, "ok_e": ok_e, "overall_ok": overall
    }
