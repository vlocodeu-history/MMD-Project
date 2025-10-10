# page_dc005.py
import math, os
from PIL import Image
import streamlit as st

# --- Bolting material allowables (MPa) from ASME II Part D Table 3 (typical values) ---
# Sa = Div.1 allowable; Sm = Div.2 allowable. You can extend/adjust easily.
BOLT_ALLOWABLES = {
    "A193 B7":   {"Sa": 172, "Sm": 172},
    "A193 B7M":  {"Sa": 138, "Sm": 138},
    "A320 L7":   {"Sa": 172, "Sm": 172},
    "A193 B16":  {"Sa": 172, "Sm": 172},
    "A320 B8 d<18":   {"Sa": 152, "Sm": 152},
    "A320 B8 20≤d<24":{"Sa": 159, "Sm": 159},
    "A320 B8 26≤d<30":{"Sa": 145, "Sm": 145},
    "A320 B8 d≈32":   {"Sa": 138, "Sm": 138},
    "A320 B8M d<18":  {"Sa": 152, "Sm": 152},
    "A320 B8M 20≤d<24":{"Sa": 152, "Sm": 152},
    "A320 B8M 26≤d<30":{"Sa": 131, "Sm": 131},
    "A320 B8M d≈32":  {"Sa": 124, "Sm": 124},
    "A453 Gr.660A":   {"Sa": 179, "Sm": 179},
}

# --- Tensile-stress areas a (mm²) for common bolt sizes (coarse metric + UNC where useful) ---
BOLT_TENSILE_AREAS_MM2 = {
    # Metric ISO coarse (approx. At per ISO 898 tables)
    "M10 × 1.5": 58.0,
    "M12 × 1.75": 84.3,     # matches your sheet
    "M16 × 2.0": 157.0,
    "M20 × 2.5": 245.0,
    "M24 × 3.0": 353.0,
    # UNC (approx., using At in² × 645.16)
    '1/2" UNC (1/2-13)': 0.1599 * 645.16,   # ≈103.2
    '5/8" UNC (5/8-11)': 0.2260 * 645.16,   # ≈145.9
    '3/4" UNC (3/4-10)': 0.3340 * 645.16,   # ≈215.5
}

def _show_dc005_image(size_px: int = 300):
    for p in ["dc005_gland.png", "assets/dc005_gland.png", "static/dc005_gland.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Body/Gland plate flange – bolting", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load DC005 image ({e}).")
            return
    st.info("Add **dc005_gland.png** (or put it in ./assets/ or ./static/) to show the drawing.")

def render_dc005():
    """
    DC005 — BOLT CALCULATION (Body/Gland plate Flange)

    Formulae:
      H  [N]  = (π/4) × (G² − Gstem²) × Pa       (Pa in MPa = N/mm²)
      Wm1[N]  = H
      Am [mm²]= Wm1 / S
      a' [mm²]= Am / n
      Ab [mm²]= a × n
      Sa_eff [MPa] = Wm1 / Ab
      Check: Sa_eff ≤ S  → VERIFIED
    """
    st.markdown("<h2 style='text-align:center;margin:0;'>BOLT CALCULATION (Body/Gland plate Flange)</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC005</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Header from Valve page
    h1, h2 = st.columns(2)
    with h1:
        st.text_input("NPS", value=str(st.session_state.get("valve_nps", "")), disabled=True)
    with h2:
        st.text_input("ASME", value=str(st.session_state.get("valve_asme_class", "")), disabled=True)

    st.markdown("### INPUT DATA")

    # Defaults pulled from session
    Pa_default = float(st.session_state.get("operating_pressure_mpa", 10.21))

    # Inputs (green cells in your sheet)
    ig1, ig2 = st.columns(2)
    with ig1:
        G = st.number_input("Gasket tight diameter  G  [mm] =", value=64.5, step=0.05, format="%.2f")
    with ig2:
        Gstem = st.number_input("Stem seal tight diameter  Gstem  [mm] =", value=27.85, step=0.05, format="%.2f")

    ip1, ip2, imat, iS = st.columns([1,1,1,1])
    with ip1:
        Pa = st.number_input("Design pressure  Pa  [MPa] =", value=Pa_default, step=0.01, format="%.2f")
    with ip2:
        Pe = st.number_input("Pressure rating – Class designation  Pe  [MPa] =", value=0.0, step=0.01, format="%.2f")
    with imat:
        mat_choices = list(BOLT_ALLOWABLES.keys())
        mat = st.selectbox("Bolt material =", mat_choices, index=1)  # default B7M
    with iS:
        S = st.number_input(
            "Allowable bolt stress, ASME VIII Div.1 App-2 (S) [MPa] =",
            value=float(BOLT_ALLOWABLES[mat]["Sa"]), step=1.0, format="%.0f"
        )

    # Optional materials table
    with st.expander("Allowable bolt stress table (ASME II Part D – Table 3)"):
        st.write({k: v for k, v in BOLT_ALLOWABLES.items()})

    # Picture
    _show_dc005_image(size_px=300)

    st.markdown("---")
    st.markdown("### DESIGN LOAD")

    # DESIGN LOAD
    ring_area = (math.pi / 4.0) * max(G**2 - Gstem**2, 0.0)   # mm²
    H = ring_area * Pa                                       # N  (since MPa = N/mm²)
    Wm1 = H

    dl1, dl2 = st.columns(2)
    with dl1:
        st.text_input("Total hydrostatic end force  H [N] = π/4 × (G² − Gstem²) × Pa =", value=f"{H:,.2f}", disabled=True)
    with dl2:
        st.text_input("Minimum required bolt load for operating condition  Wm1 [N] = H =", value=f"{Wm1:,.2f}", disabled=True)

    st.markdown("---")
    st.markdown("### BOLTS SECTION CALCULATION")

    Am = Wm1 / max(S, 1e-9)  # mm²
    bc1, bc2 = st.columns(2)
    with bc1:
        st.text_input("Limit Stress used for bolts :  S = Sa for ASME VIII Div.1", value=f"{S:.0f}", disabled=True)
    with bc2:
        st.text_input("Total required cross-sectional area of bolts  Am [mm²] = Wm1 / S =", value=f"{Am:,.3f}", disabled=True)

    st.markdown("---")
    st.markdown("### BOLTS DESIGN")

    bd1, bd2 = st.columns(2)
    with bd1:
        n = st.number_input("Bolts number  n =", value=6, min_value=1, step=1, format="%d")
    with bd2:
        a_req = Am / n
        st.text_input("Required cross-sectional area of each bolt  a' [mm²] = Am / n =", value=f"{a_req:,.3f}", disabled=True)

    bd3, bd4 = st.columns(2)
    with bd3:
        bolt_opts = list(BOLT_TENSILE_AREAS_MM2.keys())
        # pick first bolt with area >= a' (or last)
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

    # Save to state
    st.session_state["dc005"] = {
        "G_mm": G, "Gstem_mm": Gstem, "Pa_MPa": Pa, "Pe_MPa": Pe,
        "material": mat, "S_MPa": S,
        "ring_area_mm2": ring_area, "H_N": H, "Wm1_N": Wm1,
        "Am_mm2": Am, "n": n, "a_req_each_mm2": a_req,
        "bolt_size": bolt_size, "a_mm2": a, "Ab_mm2": Ab,
        "Sa_eff_MPa": Sa_eff, "verdict": verdict
    }
