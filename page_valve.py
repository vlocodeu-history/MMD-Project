import streamlit as st

def render_valve():
    ASME_RATING_MPA = {150: 2.55, 300: 5.10, 600: 10.20, 900: 15.30, 1500: 25.50, 2500: 42.50}
    NPS_BORE_MM = {0.5:15.0, 0.75:20.0, 1.0:25.0, 1.5:40.0, 2.0:51.0, 3.0:78.0, 4.0:102.0, 6.0:154.0, 8.0:202.0, 10.0:254.0, 12.0:303.0}
    F2F_MM = {(2.0,600):295}

    def calc_operating_pressure_mpa(asme_class: int) -> float:
        return float(ASME_RATING_MPA.get(asme_class, 0.0))

    def calc_bore_diameter_mm(nps: float) -> float:
        return float(NPS_BORE_MM.get(nps, round(nps*25.4, 1)))

    def calc_face_to_face_mm(nps: float, asme_class: int):
        v = F2F_MM.get((nps, asme_class))
        return int(v) if v is not None else None

    def calc_body_wall_thickness_mm(P_mpa: float, D_mm: float, S_mpa: float, CA_mm: float):
        if S_mpa <= 0 or (2*S_mpa - P_mpa) <= 0:
            return None
        t = (P_mpa * D_mm) / (2 * S_mpa - P_mpa) + CA_mm
        return round(float(t), 2)

    ALLOWABLE_STRESS_PRESETS = {
        "ASTM A350 LF2 CL.1 (Carbon Steel)": 138.0,
        "ASTM A479 UNS S31600 (SS316)": 137.0,
        "ASTM A479 UNS S31803 (Duplex 2205)": 240.0,
    }

    c1, c2 = st.columns([3,2])
    with c1:
        st.markdown("<h3 style='text-align:center;margin:0;'>VALVE DATA TRUNNION BALL VALVE</h3>", unsafe_allow_html=True)
    with c2:
        st.markdown("<h4 style='text-align:center;margin:0;'>SIDE ENTRY TYPE</h4>", unsafe_allow_html=True)
    st.markdown("---")

    left, mid, right = st.columns([1.4, 1.6, 1.4])
    with left:
        st.subheader("NPS")
        nps = st.selectbox("Nominal Pipe Size (in)",
                           options=[0.5,0.75,1.0,1.5,2.0,3.0,4.0,6.0,8.0,10.0,12.0],
                           index=4, key="valve_nps")
    with mid:
        st.subheader("ASME Class")
        asme_class = st.selectbox("Pressure Class",
                                  options=[150,300,600,900,1500,2500],
                                  index=2, key="valve_asme_class")
    with right:
        st.subheader("CALCULATION PRESSURE")
        st.caption("P (Max. Pressure Rating at Ambient) — ASME B16.34")
        P_mpa = calc_operating_pressure_mpa(asme_class)
        st.text_input("Pressure (MPa)", value=f"{P_mpa:.2f}" if P_mpa else "", disabled=True)

    st.markdown("---")

    st.markdown("### Input Parameters")
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        internal_bore_mm = st.number_input("Internal Bore (mm) (Ball/Seat)",
                                           value=float(calc_bore_diameter_mm(nps)),
                                           step=0.1, format="%.1f")
    with g2:
        f2f_default = calc_face_to_face_mm(nps, asme_class)
        face_to_face_mm = st.number_input("Face to Face (mm)",
                                          value=int(f2f_default if f2f_default is not None else 295),
                                          step=1)
    with g3:
        temp_min_c = st.number_input("Design Temperature Min (°C)", value=-29, step=1)
    with g4:
        temp_max_c = st.number_input("Design Temperature Max (°C)", value=150, step=1)

    g5, g6 = st.columns([1,3])
    with g5:
        corrosion_allowance_mm = st.number_input("Corrosion allowance (mm)", value=3.0, step=0.1, format="%.1f")
    with g6:
        st.write("")

    st.markdown("### Materials (Inputs)")
    m1, m2 = st.columns(2)
    with m1:
        body_closure = st.text_input("Body/Closure Material", value="ASTM A350 LF2 CL.1")
        ball_seat = st.text_input("Ball/Seat Material", value="ASTM A479 UNS S31600")
        stem_material = st.text_input("Stem Material", value="ASTM A479 UNS S31803")
    with m2:
        insert_material = st.text_input("Insert Material", value="DELVON V")
        bolts_material = st.text_input("Bolts Material", value="ASTM A193 B7M / ASTM A194 2HM")
        flange_ends = st.text_input("Flange Ends", value="RTJ")

    st.markdown("### Allowable Stress (for demo wall thickness calc)")
    allow_col = st.columns(2)
    with allow_col[0]:
        allow_key = st.selectbox("Preset (illustrative only)",
                                 list(ALLOWABLE_STRESS_PRESETS.keys()), index=0)
    with allow_col[1]:
        allowable_stress_mpa = st.number_input("Allowable stress (MPa)",
                                               value=float(ALLOWABLE_STRESS_PRESETS[allow_key]), step=1.0)

    st.markdown("---")
    st.markdown("## Calculated Values")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Operating Pressure (MPa)", f"{P_mpa:.2f}")
    with c2:
        st.metric("Bore Diameter (mm)", f"{internal_bore_mm:.1f}")
    with c3:
        st.metric("Face to Face (mm)", f"{face_to_face_mm:d}")

    c4, _, _ = st.columns(3)
    with c4:
        t_mm = calc_body_wall_thickness_mm(P_mpa, internal_bore_mm, allowable_stress_mpa, corrosion_allowance_mm)
        st.metric("Body Wall Thickness (mm) — demo", f"{t_mm:.2f}" if t_mm is not None else "N/A")

    st.session_state["operating_pressure_mpa"] = float(P_mpa)
    st.session_state["bore_diameter_mm"] = float(internal_bore_mm)
