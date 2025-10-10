# page_dc003.py
import math, os
from PIL import Image
import streamlit as st

# Base metal bearing material table (from your sheet)
# Values are Maximum Static Load (MPa), Maximum Dynamic Load (MPa), Max Temperature (°C)
BEARING_MATERIALS = {
    "SS316 + FRICTION COATED":         {"static": 420, "dynamic": 140, "temp": 150},
    "INCONEL 625 + FRICTION COATED":   {"static": 240, "dynamic": 140, "temp": 150},
    "MILD STEEL + FRICTION COATED":    {"static": 210, "dynamic": 140, "temp": 150},
    "INCONEL 625 HT":                   {"static": 280, "dynamic": 140, "temp": 300},
    "SS316 HT":                         {"static": 240, "dynamic": 140, "temp": 300},
}

def _show_dc003_image(size_px: int = 300):
    for p in ["dc003_bearing.png", "assets/dc003_bearing.png", "static/dc003_bearing.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Bearing sketch", use_column_width=False)
            except Exception as e:
                st.warning(f"Couldn't load bearing diagram ({e}).")
            return
    st.info("Add **dc003_bearing.png** (or put it in ./assets/ or ./static/) to show the diagram here.")

def render_dc003():
    """
    DC003 — Bearing Stress Calculation

    Formulas from the sheet:
      Sb  [mm²]  = π × Db × Hb
      BBS [MPa]  = (π × P × Dt²) / (8 × Sb)
      Check: BBS ≤ MABS (material dynamic allowable)

    Links to other pages:
      NPS, ASME Class          <- Valve page
      P (MPa)                  <- Valve page 'operating_pressure_mpa'
      Dt (seat seal diameter)  <- DC001A 'Dts_mm' if present
    """
    st.markdown("<h2 style='text-align:center;margin:0;'>Bearing Stress Calculation</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC003</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Header: show NPS / ASME if available
    h1, h2 = st.columns(2)
    with h1:
        st.text_input("Nominal Diameter  NPS [in]", value=str(st.session_state.get("valve_nps", "")), disabled=True)
    with h2:
        st.text_input("Ansi Class  CLASS", value=str(st.session_state.get("valve_asme_class", "")), disabled=True)

    # Default pressure P from valve page
    P_default = float(st.session_state.get("operating_pressure_mpa", 10.21))
    Dt_default = None
    # Prefer DC001A seat seal (Dts) if available
    if isinstance(st.session_state.get("dc001a"), dict):
        Dt_default = st.session_state["dc001a"].get("Dts_mm")
    if Dt_default is None:
        Dt_default = 71.0

    st.markdown("### INPUTS")

    i1, i2, i3, i4, i5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2])
    with i1:
        P = st.number_input("Max rating pressure  P [MPa]", value=P_default, step=0.01, format="%.2f")
    with i2:
        Dt = st.number_input("Seat seal diameter  Dt [mm]", value=float(Dt_default), step=0.1, format="%.1f")
    with i3:
        Db = st.number_input("Bearing diameter  Db [mm]", value=40.0, step=0.1, format="%.1f")
    with i4:
        Hb = st.number_input("Bearing length  Hb [mm]", value=7.0, step=0.1, format="%.1f")
    with i5:
        # material for allowable bearing stress
        mat_names = list(BEARING_MATERIALS.keys())
        mat_sel = st.selectbox("BASE METAL BEARING  MATERIAL", mat_names, index=0)

    _show_dc003_image(size_px=300)
    st.markdown("---")

    # ── Calculations
    Sb = math.pi * Db * Hb              # mm²
    BBS = (math.pi * P * (Dt ** 2)) / (8.0 * max(Sb, 1e-9))   # MPa
    MABS = float(BEARING_MATERIALS[mat_sel]["dynamic"])       # MPa (use dynamic allowable per sheet table)

    # Show design surface and stresses (match sheet fields)
    s1, s2, s3 = st.columns([1.5, 1.2, 1.2])
    with s1:
        st.text_input("Design bearing surface  Sb [mm²] = π × Db × Hb", value=f"{Sb:.4f}", disabled=True)
    with s2:
        st.text_input("Bearing stress (1)  BBS [MPa] = (π × P × Dt²) / (8 × Sb)", value=f"{BBS:.2f}", disabled=True)
    with s3:
        st.text_input("Maximum allowable bearing stress  MABS [MPa]", value=f"{MABS:.0f}", disabled=True)

    verdict = "VERIFIED" if BBS <= MABS else "NOT VERIFIED"
    st.markdown(
        f"<div style='display:flex;gap:1rem;align-items:center;margin-top:.5rem;'>"
        f"<div><b>Check:</b> BBS ≤ MABS</div>"
        f"<div style='padding:.3rem .8rem;border-radius:.4rem;background:{'#22c55e' if verdict=='VERIFIED' else '#ef4444'};color:white;font-weight:700;'>{verdict}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Optional material info table (read-only)
    with st.expander("Material table (from sheet)"):
        st.write({k: v for k, v in BEARING_MATERIALS.items()})

    # Save to state
    st.session_state["dc003"] = {
        "P_MPa": P, "Dt_mm": Dt, "Db_mm": Db, "Hb_mm": Hb,
        "Sb_mm2": Sb, "BBS_MPa": BBS, "MABS_MPa": MABS,
        "material": mat_sel, "verdict": verdict
    }
