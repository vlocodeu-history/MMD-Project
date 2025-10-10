# page_dc005a.py
import math, os
from PIL import Image
import streamlit as st

# ---- Bolt tensile-stress areas a [mm²] (ISO coarse + UNC used in your sheets)
BOLT_TENSILE_AREAS_MM2 = {
    "M10 × 1.5": 58.0,
    "M12 × 1.75": 84.3,        # used in your screenshots
    "M16 × 2.0": 157.0,
    "M20 × 2.5": 245.0,
    "M24 × 3.0": 353.0,
    '1/2" UNC (1/2-13)': 0.1599 * 645.16,   # ≈103.2
    '5/8" UNC (5/8-11)': 0.2260 * 645.16,   # ≈145.9
    '3/4" UNC (3/4-10)': 0.3340 * 645.16,   # ≈215.5
}

# ---- Bolt yield strengths Syb [MPa] for test condition (you can extend this)
BOLT_YIELD_MPA = {
    "A193 B7M": 550.0,    # your note on the sheet
    "A193 B7":  860.0,
    "A320 L7":  620.0,
    "Custom…":  550.0,
}

def _show_dc005a_image(size_px: int = 300):
    for p in ["dc005_gland.png", "assets/dc005_gland.png", "static/dc005_gland.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Body/Gland plate flange – bolting", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load DC005 image ({e}).")
            return
    st.info("Add **dc005_gland.png** (or put it in ./assets/ or ./static/) to show the drawing.")

def render_dc005a():
    """
    DC005A — Bolt calculation (Pressure × 1.5) - Test condition

    Formulas (MPa = N/mm²):
      Pa_test = 1.5 × Pa
      H  = (π/4) × (G² − Gstem²) × Pa_test
      Wm1 = H
      S  = 0.83 × Syb    (API 6D test, ASME II-D Table 3)
      Am = Wm1 / S
      a' = Am / n
      Ab = a × n
      Sa_eff = Wm1 / Ab
      Check: Sa_eff ≤ S  → VERIFIED
    """

    st.markdown("<h2 style='text-align:center;margin:0;'>BOLT CALCULATION (Body/Gland plate Flange)</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>(Pressure × 1.5) – Test condition</h4>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC005A</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # ---- Header (NPS / ASME pulled from Valve page if present)
    h1, h2 = st.columns(2)
    with h1:
        st.text_input("NPS", value=str(st.session_state.get("valve_nps", "")), disabled=True)
    with h2:
        st.text_input("ASME", value=str(st.session_state.get("valve_asme_class", "")), disabled=True)

    st.markdown("### INPUT DATA")

    # Defaults from Valve page
    Pa_base = float(st.session_state.get("operating_pressure_mpa", 10.21))  # MPa

    # Geometric inputs (green cells)
    g1, g2 = st.columns(2)
    with g1:
        G = st.number_input("O-ring tight diameter  G  [mm] =", value=64.5, step=0.05, format="%.2f")
    with g2:
        Gstem = st.number_input("Stem O-ring tight diameter  Gstem  [mm] =", value=27.85, step=0.05, format="%.2f")

    # Pressures & material
    p1, p2, m1, s1 = st.columns([1,1,1,1])
    with p1:
        Pa_test = st.number_input("Test pressure  Pa [MPa] × 1.5 =", value=round(Pa_base * 1.5, 2), step=0.01, format="%.2f")
    with p2:
        Pe = st.number_input("Pressure rating – Class designation  Pe [MPa] =", value=0.0, step=0.01, format="%.2f")
    with m1:
        mat = st.selectbox("Bolt material =", list(BOLT_YIELD_MPA.keys()), index=0, help="B7M = 550 MPa yield")
        Syb = st.number_input("Maximum yield stress at ambient temperature (bolting)  Syb [MPa]",
                              value=float(BOLT_YIELD_MPA[mat]), step=1.0)
    with s1:
        S = st.number_input("Allowable bolt stress (hydrostatic test)  S = 0.83 × Syb  [MPa]",
                            value=round(0.83 * Syb, 1), step=0.1, format="%.1f")

    # Optional note on the right (same as your sheet)
    st.caption("API 6D 25th (Test condition), ASME II Part D (Tab.3)")

    # Illustration
    _show_dc005a_image(size_px=300)

    st.markdown("---")
    st.markdown("### DESIGN LOAD")

    ring_area = (math.pi / 4.0) * max(G**2 - Gstem**2, 0.0)    # mm²
    H = ring_area * Pa_test                                   # N (MPa × mm² = N)
    Wm1 = H

    dl1, dl2 = st.columns(2)
    with dl1:
        st.text_input("Total hydrostatic end force  H [N] = π/4 × (G² − Gstem²) × Pa_test =", value=f"{H:,.1f}", disabled=True)
    with dl2:
        st.text_input("Minimum required bolt load for test condition  Wm1 [N] = H =", value=f"{Wm1:,.1f}", disabled=True)

    st.markdown("---")
    st.markdown("### BOLTS SECTION CALCULATION")

    Am = Wm1 / max(S, 1e-9)  # mm²
    bc1, bc2 = st.columns(2)
    with bc1:
        st.text_input("Limit Stress used for bolts :  Sm for ASME VIII Div.2 (test)", value=f"{S:.1f}", disabled=True)
    with bc2:
        st.text_input("Total required cross-sectional area of bolts  Am [mm²] = Wm1 / S =", value=f"{Am:,.4f}", disabled=True)

    st.markdown("---")
    st.markdown("### BOLTS DESIGN")

    bd1, bd2 = st.columns(2)
    with bd1:
        n = st.number_input("Bolts number  n =", value=6, min_value=1, step=1, format="%d")
    with bd2:
        a_req = Am / n
        st.text_input("Required cross-sectional area of each bolt  a' [mm²] = Am / n =", value=f"{a_req:,.4f}", disabled=True)

    bd3, bd4 = st.columns(2)
    with bd3:
        bolt_opts = list(BOLT_TENSILE_AREAS_MM2.keys())
        default_idx = 0
        for i, k in enumerate(bolt_opts):
            if BOLT_TENSILE_AREAS_MM2[k] >= a_req:
                default_idx = i
                break
        bolt_size = st.selectbox("We take the closest bolts having a > a'", bolt_opts, index=default_idx)
    with bd4:
        a = float(BOLT_TENSILE_AREAS_MM2[bolt_size])
        st.text_input("Bolt dimension — Actual tensile stress area  a [mm²] =", value=f"{a:,.1f}", disabled=True)

    st.markdown("---")
    st.markdown("### ACTUAL TENSILE STRESS CALCULATION")

    Ab = a * n
    Sa_eff = Wm1 / max(Ab, 1e-9)

    at1, at2 = st.columns(2)
    with at1:
        st.text_input("Total bolt tensile stress area  Ab [mm²] = a × n =", value=f"{Ab:,.1f}", disabled=True)
    with at2:
        st.text_input("Actual bolt tensile stress  Sa_eff [MPa] = Wm1 / Ab =", value=f"{Sa_eff:,.2f}", disabled=True)

    verdict = "VERIFIED" if Sa_eff <= S else "NOT VERIFIED"
    st.markdown(
        f"<div style='display:flex;gap:1rem;align-items:center;'>"
        f"<div><b>Check</b>  Sa_eff ≤ S</div>"
        f"<div style='padding:.25rem .75rem;border-radius:.4rem;background:{'#22c55e' if verdict=='VERIFIED' else '#ef4444'};color:white;font-weight:700;'>{verdict}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Save for downstream use
    st.session_state["dc005a"] = {
        "G_mm": G, "Gstem_mm": Gstem,
        "Pa_test_MPa": Pa_test, "Pe_MPa": Pe,
        "material": mat, "Syb_MPa": Syb, "S_MPa": S,
        "ring_area_mm2": ring_area, "H_N": H, "Wm1_N": Wm1,
        "Am_mm2": Am, "a_req_each_mm2": a_req, "n": n,
        "bolt_size": bolt_size, "a_mm2": a, "Ab_mm2": Ab,
        "Sa_eff_MPa": Sa_eff, "verdict": verdict
    }
