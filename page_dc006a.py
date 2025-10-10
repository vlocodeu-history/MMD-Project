# page_dc006a.py
import math, os
from PIL import Image
import streamlit as st

# Gasket catalog (extend anytime)
GASKETS = {
    "GRAPHITE": {"m": 2.0, "y": 5.0},
    "PTFE":     {"m": 3.0, "y": 14.0},
    "Non-asb.": {"m": 2.5, "y": 7.0},
}

def _img_dc006a(size_px: int = 300):
    for p in ["dc006_flange.png", "assets/dc006_flange.png", "static/dc006_flange.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Flange / gasket geometry", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load DC006A image ({e}).")
            return
    st.info("Add **dc006_flange.png** (or put it in ./assets/ or ./static/) to display the drawing.")

def render_dc006a():
    """
    DC006A — Flange Stress (ASME VIII Div.1 App.2), Test condition (Pressure × 1.5)

    Units: MPa = N/mm², dimensions in mm.

    Geometry:
      Bcd = bolt circle dia, FT = flange thickness, ESGD/ISGD = outer/inner gasket dia
      m, y = gasket factors

    Derived:
      N  = (ESGD − ISGD)/2
      b0 = N/2
      b  = b0
      G  = ESGD − 2b

    Loads:
      Pa_test = 1.5 × Pa
      H   = (π/4)·G²·Pa_test
      Hp  = 2·b·π·G·m·Pa_test
      Wm1 = H + Hp                   (operating at test pressure)
      Wm2 = π·b·G·y                  (gasket seating)

    Stress factor:
      K = (2/π)·(1 − 0.67·ESGD/Bcd)

    Stresses:
      Sf1 = K·Wm1/FT²
      Sf2 = K·Wm2/FT²
      Sf  = max(Sf1, Sf2)
    """

    st.markdown("<h2 style='text-align:center;margin:0;'>Flange Stress Calculation ASME VIII div.1 App.2 (Pressure × 1.5)</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>Test condition - DC 006A</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Defaults from previous pages
    Pa_base = float(st.session_state.get("operating_pressure_mpa", 10.21))  # MPa

    # ---- Inputs (green in your sheet)
    c1, c2, c3 = st.columns([1.1,1.1,1.1])
    with c1:
        Pa_test = st.number_input("Test pressure (1.5×) at ambient temperature Pa [MPa]",
                                  value=round(Pa_base * 1.5, 2), step=0.01, format="%.2f")
        FT   = st.number_input("Flange Thickness FT [mm]", value=23.0, step=0.1, format="%.1f")
        ISGD = st.number_input("Internal Seal Gasket Diameter ISGD [mm]", value=113.9, step=0.1, format="%.1f")
    with c2:
        Bcd  = st.number_input("Bolt circle diameter Bcd [mm]", value=142.0, step=0.1, format="%.1f")
        ESGD = st.number_input("External Seal Gasket Diameter ESGD [mm]", value=122.7, step=0.1, format="%.1f")
        gasket = st.selectbox("Gasket type", list(GASKETS.keys()), index=list(GASKETS.keys()).index("GRAPHITE"))
    with c3:
        m = st.number_input("Gasket factor m [−]", value=float(GASKETS[gasket]["m"]), step=0.1, format="%.1f")
        y = st.number_input("Gasket unit seating load y [MPa]", value=float(GASKETS[gasket]["y"]), step=0.1, format="%.1f")
        _img_dc006a(300)

    st.markdown("### GASKET LOAD REACTION DIAMETER CALCULATION G (ASME VIII DIV.1 APP.2)")

    N  = (ESGD - ISGD) / 2.0
    b0 = N / 2.0
    b  = b0
    G  = ESGD - 2.0 * b

    g1, g2, g3, g4 = st.columns(4)
    with g1: st.text_input("Gasket width N [mm] = (ESGD − ISGD)/2", value=f"{N:.2f}", disabled=True)
    with g2: st.text_input("Basic gasket seating width b0 [mm] = N/2", value=f"{b0:.2f}", disabled=True)
    with g3: st.text_input("Eff. gasket seating width b [mm]", value=f"{b:.2f}", disabled=True)
    with g4: st.text_input("Gasket load reaction diameter G [mm] = ESGD − 2b", value=f"{G:.2f}", disabled=True)

    st.markdown("### FLANGE LOAD IN OPERATING CONDITION Wm1 (ASME VIII DIV.1 APP.2) — Test pressure")

    H   = (math.pi/4.0) * (G**2) * Pa_test
    Hp  = 2.0 * b * math.pi * G * m * Pa_test
    Wm1 = H + Hp

    o1, o2, o3 = st.columns(3)
    with o1: st.text_input("Hydrostatic end force H [N] = π/4 × G² × Pa_test", value=f"{H:,.2f}", disabled=True)
    with o2: st.text_input("Joint compression load Hp [N] = 2 × b × π × G × m × Pa_test", value=f"{Hp:,.2f}", disabled=True)
    with o3: st.text_input("Min. req. bolt load at test Wm1 [N] = H + Hp", value=f"{Wm1:,.2f}", disabled=True)

    st.markdown("### FLANGE LOAD IN GASKET SEATING CONDITION Wm2 (ASME VIII DIV.1 APP.2)")
    Wm2 = math.pi * b * G * y
    st.text_input("Min. initial req. bolt load Wm2 [N] = π × b × G × y", value=f"{Wm2:,.2f}", disabled=True)

    st.markdown("### CLOSURE FLANGE STRESS CALCULATION Sf")

    K = (2.0 / math.pi) * (1.0 - 0.67 * ESGD / max(Bcd, 1e-9))
    Sf1 = K * Wm1 / max(FT, 1e-9)**2
    Sf2 = K * Wm2 / max(FT, 1e-9)**2
    Sf  = max(Sf1, Sf2)

    s1, s2, s3 = st.columns(3)
    with s1: st.text_input("Operating condition at test Sf₁ [MPa] = 2/π·(1−0.67·ESGD/Bcd)·Wm1/FT²", value=f"{Sf1:.2f}", disabled=True)
    with s2: st.text_input("Gasket seating condition Sf₂ [MPa] = 2/π·(1−0.67·ESGD/Bcd)·Wm2/FT²", value=f"{Sf2:.2f}", disabled=True)
    with s3: st.text_input("Max stress Sf [MPa] = MAX(Sf₁, Sf₂)", value=f"{Sf:.2f}", disabled=True)

    st.markdown("#### MATERIAL ALLOWABLE & CHECK")
    allow = st.number_input("Allowable stress (ALL.) [MPa] — e.g., ASTM A350 LF2 CL.1", value=161.0, step=1.0, format="%.0f")
    verdict = "OK" if Sf <= allow else "NOT OK"

    st.markdown(
        f"<div style='display:flex;gap:1rem;align-items:center;'>"
        f"<div><b>Result:</b> Sf = {Sf:.2f} MPa</div>"
        f"<div><b>Allowable:</b> {allow:.0f} MPa</div>"
        f"<div style='padding:.25rem .75rem;border-radius:.4rem;background:{'#22c55e' if verdict=='OK' else '#ef4444'};color:white;font-weight:700;'>{verdict}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Save to session
    st.session_state["dc006a"] = {
        "Pa_test_MPa": Pa_test, "Bcd_mm": Bcd, "FT_mm": FT, "ESGD_mm": ESGD, "ISGD_mm": ISGD,
        "gasket": gasket, "m": m, "y_MPa": y,
        "N_mm": N, "b0_mm": b0, "b_mm": b, "G_mm": G,
        "H_N": H, "Hp_N": Hp, "Wm1_N": Wm1, "Wm2_N": Wm2,
        "K": K, "Sf1_MPa": Sf1, "Sf2_MPa": Sf2, "Sf_MPa": Sf,
        "allow_MPa": allow, "verdict": verdict
    }
