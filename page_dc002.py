# page_dc002.py
import math
import os
from PIL import Image
import streamlit as st

# Tensile stress areas for common bolts (UNC + a few metric) in mm²
# source: standard tensile-stress-area tables (e.g., ASME/ISO conversion; 1 in² = 645.16 mm²)
BOLT_TENSILE_AREAS_MM2 = {
    # UNC (coarse)
    '1/2" UNC (1/2-13)': 0.1599 * 645.16,   # ≈ 103.2
    '5/8" UNC (5/8-11)': 0.2260 * 645.16,   # ≈ 145.9   (your sheet ≈ 145.8)
    '3/4" UNC (3/4-10)': 0.3340 * 645.16,   # ≈ 215.5
    '7/8" UNC (7/8-9)':  0.4620 * 645.16,   # ≈ 298.1
    '1" UNC (1-8)':      0.6060 * 645.16,   # ≈ 391.0
    # Metric (ISO coarse) – approximate tensile-stress areas
    'M16 × 2.0 (coarse)': 157.0,
    'M20 × 2.5 (coarse)': 245.0,
    'M24 × 3.0 (coarse)': 353.0,
}

# Allowable bolt stress presets, MPa (N/mm²)
ALLOWABLE_S_BY_MATERIAL = {
    "A193 B7M": 138.0,   # value shown on your sheet
    "A193 B7":  172.0,
    "A320 L7":  138.0,
    "Custom…":  138.0,   # default; user can override
}

def _show_flange_image(size_px: int = 300):
    """Show the flange image at a fixed square size (default 300×300)."""
    paths = ["dc002_flange.png", "assets/dc002_flange.png", "static/dc002_flange.png"]
    for p in paths:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Body-Closure with bolting", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load flange image ({e}).")
            return
    st.info("Add **dc002_flange.png** (or put it in ./assets/ or ./static/) to show the sheet picture here.")

def render_dc002():
    """
    DC002 — Body-Closure Bolts calculation

    Formulas (as on your sheet):
      H  [N]  = 0.785 × G² × Pa      (0.785 ≈ π/4)
      Wm1[N]  = H
      Am [mm²]= Wm1 / S
      a' [mm²]= Am / n
      Ab [mm²]= a × n
      Sa_eff [MPa] = Wm1 / Ab
      Check: Sa_eff ≤ S  → VERIFIED
    """
    st.markdown("<h2 style='text-align:center;margin:0;'>Body-Closure Bolts calculation</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC002</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # ───────────────── Header: NPS / ASME (from Valve page if available)
    header1, header2 = st.columns(2)
    with header1:
        nps = st.session_state.get("valve_nps", None)
        st.text_input("NPS", value=str(nps) if nps is not None else "", disabled=True)
    with header2:
        asme = st.session_state.get("valve_asme_class", None)
        st.text_input("ASME", value=str(asme) if asme is not None else "", disabled=True)

    st.markdown("### INPUT DATA")

    # Defaults from previous pages
    Pa_default = float(st.session_state.get("operating_pressure_mpa", 10.21))  # MPa (N/mm²)

    col_g, col_pa, col_pe = st.columns([1.2, 1, 1])
    with col_g:
        # Gasket tight diameter (user input; your sheet shows 122.7 mm)
        G = st.number_input("Gasket tight diameter  G  [mm] =", value=122.7, step=0.1, format="%.1f")
    with col_pa:
        Pa = st.number_input("Design pressure  Pa  [MPa] =", value=Pa_default, step=0.01, format="%.2f")
    with col_pe:
        Pe = st.number_input("Pressure rating – Class designation  Pe  [MPa] =", value=0.0, step=0.01, format="%.2f")

    col_mat, col_s = st.columns([1.2, 1])
    with col_mat:
        bolt_mat = st.selectbox("Bolt material =", list(ALLOWABLE_S_BY_MATERIAL.keys()), index=0)
    with col_s:
        S = st.number_input(
            "Allowable bolt stress, for ASME VIII div.1-App.2-2023  S  [MPa] =",
            value=float(ALLOWABLE_S_BY_MATERIAL[bolt_mat]), step=1.0, format="%.0f"
        )

    # Image (optional)
    _show_flange_image(size_px=300)

    st.markdown("---")
    st.markdown("### DESIGN LOAD")

    # DESIGN LOAD
    # H = 0.785 × G² × Pa  (with Pa in N/mm²)
    H = 0.785 * (G ** 2) * Pa
    Wm1 = H

    col_h, col_wm1 = st.columns(2)
    with col_h:
        st.text_input("Total hydrostatic end force  H [N] = 0.785 × G² × Pa =", value=f"{H:,.2f}", disabled=True)
    with col_wm1:
        st.text_input("Minimum required bolt load for operating condition  Wm1 [N] =", value=f"{Wm1:,.2f}", disabled=True)

    st.markdown("---")
    st.markdown("### BOLTS SECTION CALCULATION")

    Am = Wm1 / max(S, 1e-9)  # mm²
    col_s2, col_am = st.columns(2)
    with col_s2:
        st.text_input("Limit stress used for bolts :  S = Sa for ASME VIII Div.1", value=f"{S:.0f}", disabled=True)
    with col_am:
        st.text_input("Total required cross-sectional area of bolts  Am [mm²] = Wm1 / S =", value=f"{Am:,.2f}", disabled=True)

    st.markdown("---")
    st.markdown("### BOLTS DESIGN")

    # Number of bolts
    col_n, col_areq = st.columns(2)
    with col_n:
        n = st.number_input("Bolts number  n =", value=6, min_value=1, step=1, format="%d")
    with col_areq:
        a_req_each = Am / n
        st.text_input("Required cross-sectional area of each bolt  a' [mm²] = Am / n =", value=f"{a_req_each:,.2f}", disabled=True)

    # Choose closest bolt size having a > a'
    col_sel, col_a = st.columns(2)
    with col_sel:
        # pick the first size whose area >= a_req_each; else default to last
        bolt_options = list(BOLT_TENSILE_AREAS_MM2.keys())
        default_idx = 0
        for i, k in enumerate(bolt_options):
            if BOLT_TENSILE_AREAS_MM2[k] >= a_req_each:
                default_idx = i
                break
        bolt_size = st.selectbox("We take the closest bolts having a > a'", bolt_options, index=default_idx)
    with col_a:
        a = float(BOLT_TENSILE_AREAS_MM2[bolt_size])
        st.text_input("Bolt dimension  —  Actual tensile stress area  a [mm²] =", value=f"{a:,.1f}", disabled=True)

    st.markdown("---")
    st.markdown("### ACTUAL TENSILE STRESS CALCULATION")

    Ab = a * n
    Sa_eff = Wm1 / max(Ab, 1e-9)

    col_ab, col_saeff = st.columns(2)
    with col_ab:
        st.text_input("Total bolt tensile stress area  Ab [mm²] = a × n =", value=f"{Ab:,.1f}", disabled=True)
    with col_saeff:
        st.text_input("Actual bolt tensile stress  Sa_eff [MPa] = Wm1 / Ab =", value=f"{Sa_eff:,.2f}", disabled=True)

    # Check
    verdict = "VERIFIED" if Sa_eff <= S else "NOT VERIFIED"
    st.markdown(
        f"<div style='display:flex;gap:1rem;align-items:center;'>"
        f"<div><b>Check</b>  Sa_eff ≤ S</div>"
        f"<div style='padding:.25rem .75rem;border-radius:.4rem;background:{'#22c55e' if verdict=='VERIFIED' else '#ef4444'};color:white;font-weight:700;'>{verdict}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Save to state for downstream use
    st.session_state["dc002"] = {
        "G_mm": G, "Pa_MPa": Pa, "Pe_MPa": Pe, "bolt_material": bolt_mat, "S_MPa": S,
        "H_N": H, "Wm1_N": Wm1, "Am_mm2": Am, "n": n, "a_req_each_mm2": a_req_each,
        "bolt_size": bolt_size, "a_mm2": a, "Ab_mm2": Ab, "Sa_eff_MPa": Sa_eff, "verdict": verdict
    }
