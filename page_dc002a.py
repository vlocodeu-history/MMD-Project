# page_dc002a.py
import math, os
from PIL import Image
import streamlit as st

# Tensile-stress areas (mm²) for common bolt sizes (UNC + a few metric)
BOLT_TENSILE_AREAS_MM2 = {
    '1/2" UNC (1/2-13)': 0.1599 * 645.16,   # ≈ 103.2
    '5/8" UNC (5/8-11)': 0.2260 * 645.16,   # ≈ 145.9
    '3/4" UNC (3/4-10)': 0.3340 * 645.16,   # ≈ 215.5
    '7/8" UNC (7/8-9)':  0.4620 * 645.16,   # ≈ 298.1
    '1" UNC (1-8)':      0.6060 * 645.16,   # ≈ 391.0
    'M16 × 2.0': 157.0, 'M20 × 2.5': 245.0, 'M24 × 3.0': 353.0,
}

# Bolt materials -> yield strength Syb (MPa). You can extend this list easily.
BOLT_YIELD_MPA = {
    "A193 B7M": 550.0,   # your sheet note
    "A193 B7":  860.0,
    "A320 L7":  620.0,
    "Custom…": 550.0,
}

def _show_flange_image(size_px: int = 300):
    for p in ["dc002_flange.png", "assets/dc002_flange.png", "static/dc002_flange.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Body-Closure with bolting", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load flange image ({e}).")
            return
    st.info("Add **dc002_flange.png** (or put it in ./assets/ or ./static/) to show the sheet picture here.")

def render_dc002a():
    """
    DC002A — Body-Closure Bolts calculation (Pressure × 1.5) - Test condition

    Formulas:
      Pa_test [MPa] = 1.5 × Pa
      H [N]         = 0.785 × G² × Pa_test
      Wm1 [N]       = H
      S [MPa]       = 0.83 × Syb   (hydrostatic test, API 6D 25th / ASME II-D)
      Am [mm²]      = Wm1 / S
      a' [mm²]      = Am / n
      Ab [mm²]      = a × n
      Sa_eff [MPa]  = Wm1 / Ab
      Check         : Sa_eff ≤ S  → VERIFIED
    """

    st.markdown("<h2 style='text-align:center;margin:0;'>Body-Closure Bolts calculation (Pressure × 1.5) — Test condition</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC002A</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Header (NPS/ASME from Valve page if available)
    h1, h2 = st.columns(2)
    with h1:
        st.text_input("NPS", value=str(st.session_state.get("valve_nps", "")), disabled=True)
    with h2:
        st.text_input("ASME", value=str(st.session_state.get("valve_asme_class", "")), disabled=True)

    st.markdown("### INPUT DATA")

    # Pull base Pa from Valve page, compute test pressure
    Pa_base = float(st.session_state.get("operating_pressure_mpa", 10.21))
    g_col, pa_col, pe_col = st.columns([1.2, 1, 1])
    with g_col:
        G = st.number_input("Gasket tight diameter  G  [mm] =", value=122.7, step=0.1, format="%.1f")
    with pa_col:
        Pa_test = st.number_input("Test pressure  Pa [MPa] × 1.5 =", value=round(Pa_base * 1.5, 2), step=0.01, format="%.2f")
    with pe_col:
        Pe = st.number_input("Pressure rating – Class designation  Pe  [MPa] =", value=0.0, step=0.01, format="%.2f")

    m_col, s_col = st.columns([1.2, 1])
    with m_col:
        mat = st.selectbox("Bolt material =", list(BOLT_YIELD_MPA.keys()), index=0, help="B7M = 550 MPa yield")
        Syb = st.number_input("Maximum yield stress at ambient temperature (bolting)  Syb  [MPa]", value=float(BOLT_YIELD_MPA[mat]), step=1.0)
    with s_col:
        S = st.number_input("Allowable bolt stress (hydro test)  S = 0.83 × Syb  [MPa]",
                            value=round(0.83 * Syb, 1), step=0.1, format="%.1f")

    _show_flange_image(size_px=300)

    st.markdown("---")
    st.markdown("### DESIGN LOAD")

    H = 0.785 * (G ** 2) * Pa_test
    Wm1 = H

    dl1, dl2 = st.columns(2)
    with dl1:
        st.text_input("Total hydrostatic end force  H [N] = 0.785 × G² × Pa_test =", value=f"{H:,.2f}", disabled=True)
    with dl2:
        st.text_input("Minimum required bolt load for test condition  Wm1 [N] =", value=f"{Wm1:,.2f}", disabled=True)

    st.markdown("---")
    st.markdown("### BOLTS SECTION CALCULATION")

    Am = Wm1 / max(S, 1e-9)  # mm²
    bc1, bc2 = st.columns(2)
    with bc1:
        st.text_input("Limit Stress used for bolts :  S = Sm for ASME VIII Div.2", value=f"{S:.1f}", disabled=True)
    with bc2:
        st.text_input("Total required cross-sectional area of bolts  Am [mm²] = Wm1 / S =", value=f"{Am:,.2f}", disabled=True)

    st.markdown("---")
    st.markdown("### BOLTS DESIGN")

    bd1, bd2 = st.columns(2)
    with bd1:
        n = st.number_input("Bolts number  n =", value=6, min_value=1, step=1, format="%d")
    with bd2:
        a_req_each = Am / n
        st.text_input("Required cross-sectional area of each bolt  a' [mm²] = Am / n =", value=f"{a_req_each:,.2f}", disabled=True)

    bd3, bd4 = st.columns(2)
    with bd3:
        options = list(BOLT_TENSILE_AREAS_MM2.keys())
        # choose first bolt with area >= a' (or last if none)
        default_idx = 0
        for i, k in enumerate(options):
            if BOLT_TENSILE_AREAS_MM2[k] >= a_req_each:
                default_idx = i
                break
        bolt_size = st.selectbox("We take the closest bolts having a > a'", options, index=default_idx)
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

    st.session_state["dc002a"] = {
        "G_mm": G, "Pa_test_MPa": Pa_test, "Pe_MPa": Pe,
        "bolt_material": mat, "Syb_MPa": Syb, "S_MPa": S,
        "H_N": H, "Wm1_N": Wm1, "Am_mm2": Am,
        "n": n, "a_req_each_mm2": a_req_each,
        "bolt_size": bolt_size, "a_mm2": a, "Ab_mm2": Ab,
        "Sa_eff_MPa": Sa_eff, "verdict": verdict
    }
