import os
from PIL import Image
import streamlit as st

def _show_dc004_image(size_px: int = 300):
    for p in ["dc004_seat_section.png", "assets/dc004_seat_section.png", "static/dc004_seat_section.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Seat section / load sketch", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load DC004 diagram ({e}).")
            return
    st.info("Add **dc004_seat_section.png** (or put it in ./assets/ or ./static/) to show the sketch here.")

def render_dc004():
    st.markdown("<h2 style='text-align:center;margin:0;'>Seat Thickness Calculation ASME VIII Div.1, ASME VIII Div.2</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC004</h4>", unsafe_allow_html=True)
    st.caption("REFERENCES: ASME II PART. D TABLE 1A Ed.2023 · ASME VIII DIV.1 UG-27 · ASME VIII DIV.2: Sm")
    st.markdown("---")

    # Header (from Valve page if available)
    c1, c2, _ = st.columns([1,1,2])
    with c1:
        st.text_input("NPS", value=str(st.session_state.get("valve_nps", "")), disabled=True)
    with c2:
        st.text_input("Valve Class", value=str(st.session_state.get("valve_asme_class", "")), disabled=True)

    st.markdown("### INPUT DATA")

    # Allowables (editable)
    col_a1, col_a2, col_img = st.columns([1.1, 1.1, 2.2])
    with col_a1:
        SmF316 = st.number_input("LIMIT VALUES — ASME VIII, Div.2  SmF316 [MPa]", value=138.0, step=1.0, format="%.0f")
    with col_a2:
        SaF316 = st.number_input("LIMIT VALUES — ASME VIII, Div.1  SaF316 [MPa]", value=138.0, step=1.0, format="%.0f")
    with col_img:
        _show_dc004_image(size_px=300)

    # Geometry & pressures (editable)
    P_default  = float(st.session_state.get("operating_pressure_mpa", 10.21))
    Di_default = float(st.session_state.get("bore_diameter_mm", 51.00))
    col_i1, col_i2, col_i3 = st.columns([1.1, 1.1, 1.1])
    with col_i1:
        Di = st.number_input("INTERNAL SEAT DIAM.  Di [mm]", value=Di_default, step=0.01, format="%.2f")
    with col_i2:
        P  = st.number_input("DESIGN PRESSURE  P [MPa]", value=P_default, step=0.01, format="%.2f")
    with col_i3:
        PT = st.number_input("SEAT TEST PRESSURE  PT = 1.1 × P [MPa]", value=round(1.1 * P, 2), step=0.01, format="%.2f")

    st.markdown("---")

    # DESIGN CONDITION — Div.1 (dynamic)
    st.markdown("#### DESIGN CONDITION: ASME VIII, DIV.1 — Ed.2023")
    st.caption("MINIMUM THK. FOR F316 MATERIAL")
    denom_d1 = 2.0 * (SaF316 - 0.6 * P)
    t_design = (P * Di) / denom_d1 if denom_d1 > 0 else float("nan")
    st.text_input("t = ( P × Di ) / ( 2 × ( SaF316 − 0.6 × P ) )", value=f"{t_design:.2f}", disabled=True)

    # SEAT TEST CONDITION — Div.2 (dynamic)
    st.markdown("#### SEAT TEST CONDITION: ASME VIII, DIV.2 — Ed.2023")
    st.caption("MINIMUM THK. FOR F316 MATERIAL")
    denom_d2 = 2.0 * (SmF316 - 0.6 * PT)
    t_test = (PT * Di) / denom_d2 if denom_d2 > 0 else float("nan")
    st.text_input("t = ( PT × Di ) / ( 2 × ( SmF316 − 0.6 × PT ) )", value=f"{t_test:.2f}", disabled=True)

    st.markdown("---")

    # Real thickness (currently fixed per your spec; make editable by replacing disabled=True and value=…)
    real_t = 6.90
    st.text_input("REAL THICKNESS  [mm]", value=f"{real_t:.2f}", disabled=True)
    # If you want it editable instead, use:
    # real_t = st.number_input("REAL THICKNESS  [mm]", value=6.90, step=0.05, format="%.2f")

    req_t  = max(t_design, t_test)
    verdict = "VERIFIED" if (not (req_t != req_t)) and real_t >= req_t else "NOT VERIFIED"  # NaN-safe

    st.markdown(
        f"<div style='display:flex;gap:1rem;align-items:center;'>"
        f"<div>Required minimum thickness = <b>{req_t:.2f} mm</b></div>"
        f"<div style='padding:.25rem .75rem;border-radius:.4rem;background:{'#22c55e' if verdict=='VERIFIED' else '#ef4444'};color:white;font-weight:700;'>{verdict}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.caption("Dimensions in mm · Pressure in MPa")

    # persist (useful for other sheets)
    st.session_state["dc004"] = {
        "Di_mm": Di, "P_MPa": P, "PT_MPa": PT,
        "SaF316_MPa": SaF316, "SmF316_MPa": SmF316,
        "t_design_mm": t_design, "t_test_mm": t_test,
        "real_t_mm": real_t, "required_t_mm": req_t, "verdict": verdict,
    }
