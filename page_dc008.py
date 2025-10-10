# page_dc008.py
import math
import os
from PIL import Image
import streamlit as st

# -----------------------------
# Class tables (from your sheet)
# -----------------------------
# Minimum yield stress required for the selected material [MPa]
REQ_SY = {
    "150-600": 170.00,
    "900":     205.00,
    "1500":    250.00,
    "2500":    300.00,
}
# Minimum ratio D/B required
REQ_DB = {
    "150-600": 1.50,
    "900":     1.55,
    "1500":    1.60,
    "2500":    1.70,
}
CLASS_LEVELS = ["150-600", "900", "1500", "2500"]


def _class_to_band(asme_class: int) -> str:
    """
    Map a numeric class (e.g., 600) to one of the dropdown bands:
    '150-600', '900', '1500', or '2500'.
    """
    if asme_class <= 600:
        return "150-600"
    if asme_class <= 900:
        return "900"
    if asme_class <= 1500:
        return "1500"
    return "2500"


def _show_dc008_image(size_px: int = 300):
    for p in ["dc008_ball.png", "assets/dc008_ball.png", "static/dc008_ball.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Ball / bore geometry (schematic)", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load DC008 diagram ({e}).")
            return
    st.info("Add **dc008_ball.png** (or put it in ./assets/ or ./static/) to show the sketch here.")


def render_dc008():
    """
    DC008 — BALL SIZING CALCULATION

    Inputs (green on sheet):
      Pr [MPa]        – design pressure (MPa = N/mm²)           ← from Valve Data if present
      D_ball [mm]     – external spherical ball diameter
      B [mm]          – internal bore diameter                   ← often 51 mm for the example
      α [deg]         – contact angle (stored)
      Material, Sy    – material yield stress
      H [mm]          – distance of flat top from centerline

    Derived:
      T = H − B/2  (ball thickness at top region)
      D/B actual ratio
      Allowable Sy(min) and (D/B)min by selected Class (dropdowns)
      Shell stress at top: St1a = Pr × [ 0.5×(B/T) + 0.6 ]
      Allowable = 2/3 × Sy
      Checks: St1a ≤ 2/3 Sy ;  Sy ≥ Sy(min) ;  D/B ≥ (D/B)min
    """
    st.markdown("<h2 style='text-align:center;margin:0;'>BALL SIZING CALCULATION</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC008</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # ---- Defaults from earlier pages
    asme_cls_num = int(st.session_state.get("valve_asme_class", 600))
    asme_cls_band_default = _class_to_band(asme_cls_num)
    Pr_default = float(st.session_state.get("operating_pressure_mpa", 10.21))
    B_default = float(st.session_state.get("bore_diameter_mm", 51.0))

    # ---- Inputs block (like the sheet)
    c0, c1, c2 = st.columns([1.2, 1.2, 1.2])
    with c0:
        Pr = st.number_input("Design pressure Pr [MPa]", value=Pr_default, step=0.01, format="%.2f")
        D_ball = st.number_input("Ball diameter D ball [mm]", value=88.95, step=0.01, format="%.2f",
                                 help="External spherical ball diameter")
        B = st.number_input("Bore diameter B [mm]", value=B_default, step=0.1, format="%.1f")
        alpha_deg = st.number_input("Contact angle α [deg]", value=45.0, step=0.5, format="%.1f")
    with c1:
        ball_material = st.text_input("Ball Material", value="ASTM A479 UNS S31600")
        Sy = st.number_input("Yield stress Sy [MPa]", value=205.0, step=1.0, format="%.0f",
                             help="Select from material sheet; used for 2/3 Sy check")
        H = st.number_input("Distance of flat top from Centerline H [mm]", value=32.5, step=0.1, format="%.1f")
        T = H - B / 2.0  # thickness at top
        st.text_input("Ball thickness in the top region T [mm] = H − B/2", value=f"{T:.3f}", disabled=True)
    with c2:
        _show_dc008_image(300)
        st.text_input("Valve Class (from Valve Data)", value=str(asme_cls_num), disabled=True)

    # ------------------------------
    # SIZING CRITERIA (dropdowns)
    # ------------------------------
    st.markdown("### SIZING CRITERIA")

    cSY, cDB = st.columns(2)
    with cSY:
        cls_yield = st.selectbox(
            "Minimum Yield stress of selected material (MPa) — pick Class",
            CLASS_LEVELS,
            index=CLASS_LEVELS.index(asme_cls_band_default)
        )
        req_Sy_min = REQ_SY[cls_yield]
        st.text_input("Required Sy(min) [MPa]", value=f"{req_Sy_min:.2f}", disabled=True)
    with cDB:
        cls_ratio = st.selectbox(
            "Minimum Ratio Spherical Diameter / internal Bore — pick Class",
            CLASS_LEVELS,
            index=CLASS_LEVELS.index(asme_cls_band_default)
        )
        req_DB_min = REQ_DB[cls_ratio]
        st.text_input("Required (D/B)min", value=f"{req_DB_min:.3f}", disabled=True)

    # Actual D/B from current inputs
    actual_DB = (D_ball / B) if B else float("nan")
    st.text_input("Actual Ratio  D / B", value=f"{actual_DB:.2f}", disabled=True)

    ok_sy = Sy >= req_Sy_min
    ok_db = actual_DB >= req_DB_min

    st.markdown(
        f"<div style='display:flex;gap:1rem;font-weight:700;'>"
        f"<div>Sy ≥ {req_Sy_min:.2f} MPa → "
        f"<span style='color:{'#16a34a' if ok_sy else '#dc2626'}'>{'OK' if ok_sy else 'NOT OK'}</span></div>"
        f"<div>D/B ≥ {req_DB_min:.2f} → "
        f"<span style='color:{'#16a34a' if ok_db else '#dc2626'}'>{'OK' if ok_db else 'NOT OK'}</span></div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # ------------------------------
    # SHELL STRESS CALCULATION St1
    # ------------------------------
    st.markdown("### SHELL STRESS CALCULATION St1  \naccording to ASME VIII DIV.1 Ed.2023 / Appendix 1 Ed.2023")

    if T <= 0:
        St1a = float("nan")
    else:
        # Circumferential (hoop) stress at top of ball from your sheet
        St1a = Pr * (0.5 * (B / T) + 0.6)

    allow_23Sy = (2.0 / 3.0) * Sy

    k1, k2, k3 = st.columns([1.1, 1.1, 1.1])
    with k1:
        st.text_input("Circumferential stress St1a [MPa] = Pr × [ 0.5 × B/T + 0.6 ]",
                      value=f"{St1a:.2f}", disabled=True)
    with k2:
        st.text_input("Allowable limit: 2/3 Yield stress [MPa]",
                      value=f"{allow_23Sy:.2f}", disabled=True)
    with k3:
        verdict = "OK" if (not (St1a != St1a)) and (St1a <= allow_23Sy) else "NOT OK"
        st.text_input("Circumferential stress in the top of the ball ≤ 2/3 Sy",
                      value=verdict, disabled=True)

    # Persist for downstream use
    st.session_state["dc008"] = {
        "Pr_MPa": Pr, "D_ball_mm": D_ball, "B_mm": B, "alpha_deg": alpha_deg,
        "material": ball_material, "Sy_MPa": Sy, "H_mm": H, "T_mm": T,
        "criteria_class_yield": cls_yield, "criteria_class_ratio": cls_ratio,
        "req_Sy_min": req_Sy_min, "req_DB_min": req_DB_min,
        "actual_DB": actual_DB, "St1a_MPa": St1a, "allow_23Sy_MPa": allow_23Sy,
        "check_sy": ok_sy, "check_db": ok_db, "verdict": verdict
    }
