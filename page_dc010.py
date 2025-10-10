# page_dc010.py
import math, os
from PIL import Image
import streamlit as st

def _img_dc010(size_px: int = 300):
    for p in ["dc010_torque.png", "assets/dc010_torque.png", "static/dc010_torque.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Torque components (schematic)", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load DC010 diagram ({e}).")
            return
    st.info("Add **dc010_torque.png** (or put it in ./assets/ or ./static/) to show a sketch here.")

def render_dc010():
    """
    DC010 — VALVE TORQUE CALCULATION

    Inputs (green on your sheet) and defaults sourced from other pages when present:
      Valve class → session 'valve_asme_class'
      Operating pressure Po [MPa] → session 'operating_pressure_mpa'
      Ball diameter D [mm] → from DC008 'D_ball_mm'
      External seal diameter Dc [mm] → often 71 (from DC001A 'Dts')
      Seat friction radius b1 [mm] → 31.74 (sheet)
      Contact diameter Dm [mm] → from DC001 'Dm_mm' (≈ 62.3 in examples)
      Internal ball bushing diameter Db [mm]
      Spring force Pr [Fmr] [N] → from DC001 total spring load each seat (≈ 787 N)
      Qty. of springs per seat Nma → from DC001 (default 1)
      Coefficients: f1 (ball–bushing), f2 (ball–seat)

    Calculations (MPa = N/mm²):
      Fb   = (π · Dc² / 4) · Po                          [N]   pressure load on ball hubs
      Mtb  = Fb · f1 · Db / 2                            [N·mm] torque from differential pressure
      Fm   = Pr · Nma                                    [N]    spring load on each seat (per seat in sheet)
      Mtm  = 2 · Fm · f2 · 0.91 · (D/2)                  [N·mm] torque from spring load (two seats)
      Fi   = (π · (Dc² − Dm²) / 4) · Po                  [N]    piston effect
      Mti  = Fi · f2 · 0.91 · (D/2)                      [N·mm] torque from piston effect
      Tbb1 = (Mtb + Mtm + Mti) / 1000                    [N·m]  total (divide by 1000 to convert N·mm → N·m)
    """

    st.markdown("<h2 style='text-align:center;margin:0;'>VALVE TORQUE CALCULATION</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC010</h4>", unsafe_allow_html=True)
    st.markdown("### VALVE TORQUE CALCULATION")

    # ---- Defaults from session (if earlier pages were used)
    valve_class = int(st.session_state.get("valve_asme_class", 600))
    Po_default  = float(st.session_state.get("operating_pressure_mpa", 10.21))
    D_default   = float(st.session_state.get("dc008", {}).get("D_ball_mm",
                      st.session_state.get("D_ball_mm", 88.95)))
    Dc_default  = float(st.session_state.get("dc001a", {}).get("Dts_mm", 71.0))  # from DC001A if you saved it
    Dm_default  = float(st.session_state.get("dc001", {}).get("inputs", {}).get("Dm_mm",
                      st.session_state.get("Dm_mm", 62.3)))
    Db_default  = 40.0
    Pr_default  = float(st.session_state.get("dc001", {}).get("computed", {}).get("F_real_total_N",
                      st.session_state.get("Fmr_N", 787.0)))
    Nma_default = int(st.session_state.get("dc001", {}).get("inputs", {}).get("n_proj",
                      st.session_state.get("Nma", 1)))

    # ---- Inputs (match sheet order)
    c1, c2, c3 = st.columns([1.1, 1.1, 1.1])
    with c1:
        st.text_input("Valve class =", value=str(valve_class), disabled=True)
        Po = st.number_input("Operating pressure Po [MPa] =", value=Po_default, step=0.01, format="%.2f")
        D  = st.number_input("Ball diameter D [mm] =", value=D_default, step=0.01, format="%.2f")
        Dc = st.number_input("External seal diameter Dc [mm] =", value=Dc_default, step=0.1, format="%.1f")
    with c2:
        b1 = st.number_input("Seat friction radius b1 [mm] =", value=31.74, step=0.01, format="%.2f")
        Dm = st.number_input("Contact diameter Dm [mm] =", value=Dm_default, step=0.01, format="%.2f")
        Db = st.number_input("Internal ball bushing diameter Db [mm] =", value=Db_default, step=0.1, format="%.1f")
        Pr = st.number_input("Spring force Pr [Fmr] [N] =", value=Pr_default, step=0.1, format="%.1f")
    with c3:
        Nma = st.number_input("Q.ty of springs Nma (for each seat) =", value=Nma_default, step=1, min_value=1)
        f1  = st.number_input("Coeff. of friction between ball and ball bushing f1 =", value=0.03, step=0.01, format="%.2f")
        f2  = st.number_input("Coeff. of friction between ball and seat f2 =", value=0.15, step=0.01, format="%.2f")
        _img_dc010(300)

    st.markdown("----")
    st.markdown("#### Break to open torque calculation in single piston effect condition Tbb1")

    # ---- Calculations
    # Pressure load on ball hubs
    Fb = (math.pi * (Dc**2) / 4.0) * Po  # N (since Po in MPa = N/mm^2 and Dc in mm)
    # Torque from differential pressure (convert to N·m at output)
    Mtb_Nmm = Fb * f1 * (Db / 2.0)       # N·mm

    # Spring load on each seat and torque from both seats
    Fm = Pr * Nma                        # N
    Mtm_Nmm = 2.0 * Fm * f2 * 0.91 * (D / 2.0)  # N·mm

    # Piston effect and corresponding torque
    Fi = (math.pi * (max(Dc**2 - Dm**2, 0.0)) / 4.0) * Po   # N
    Mti_Nmm = Fi * f2 * 0.91 * (D / 2.0)                    # N·mm

    # Total torque in N·m (sum N·mm / 1000)
    Tbb1_Nm = (Mtb_Nmm + Mtm_Nmm + Mti_Nmm) / 1000.0

    # ---- Output table (right column numbers as in sheet)
    r1, r2, r3 = st.columns([1, 1, 1])
    with r1:
        st.text_input("Pressure load on ball hubs Fb [N]", value=f"{Fb:,.0f}", disabled=True)
        st.text_input("Torque from total differential pressure Mtb [N·m]",
                      value=f"{Mtb_Nmm/1000.0:,.0f}", disabled=True)
        st.text_input("Spring load on each seat Fm [N]", value=f"{Fm:,.0f}", disabled=True)
        st.text_input("Torque from spring load (two seats) Mtm [N·m]",
                      value=f"{Mtm_Nmm/1000.0:,.0f}", disabled=True)
        st.text_input("Piston effect Fi [N]", value=f"{Fi:,.0f}", disabled=True)
        st.text_input("Torque from piston effect Mti [N·m]",
                      value=f"{Mti_Nmm/1000.0:,.0f}", disabled=True)
    with r2:
        pass
    with r3:
        st.text_input("Total torque  Tbb1  [N·m] = (Mtb + Mtm + Mti)",
                      value=f"{Tbb1_Nm:,.0f}", disabled=True)

    # Save to session for reports/export
    st.session_state["dc010"] = {
        "valve_class": valve_class, "Po_MPa": Po,
        "D_mm": D, "Dc_mm": Dc, "b1_mm": b1, "Dm_mm": Dm, "Db_mm": Db,
        "Pr_N": Pr, "Nma": int(Nma), "f1": f1, "f2": f2,
        "Fb_N": Fb, "Mtb_Nm": Mtb_Nmm/1000.0, "Fm_N": Fm,
        "Mtm_Nm": Mtm_Nmm/1000.0, "Fi_N": Fi, "Mti_Nm": Mti_Nmm/1000.0,
        "Tbb1_Nm": Tbb1_Nm
    }
