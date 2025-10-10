# page_dc012.py
import math
import pandas as pd
import streamlit as st

# ---- Table from the sheet (UNI-ISO 3266) ----
THREADS = ["M8", "M10", "M12", "M16", "M20", "M24", "M30", "M36", "M42", "M48", "M56"]

# Cross-sectional areas A [mm^2]
AREA_MAP = {
    "M8": 36, "M10": 58, "M12": 84, "M16": 157, "M20": 245,
    "M24": 353, "M30": 561, "M36": 817, "M42": 1120, "M48": 1470, "M56": 2030
}

# Rated load per eye bolt [kg] (UNI-ISO 3266) – straight (0°) and at 45°
RATED_0_MAP = {  # CARICO CON TIRO DIRITTO (kg)
    "M8": 140, "M10": 230, "M12": 340, "M16": 700, "M20": 1200,
    "M24": 1800, "M30": 3600, "M36": 5100, "M42": 7000, "M48": 8600, "M56": None  # not shown in sheet
}
RATED_45_MAP = {  # CARICO CON TIRO A 45° (kg)
    "M8": 95, "M10": 170, "M12": 240, "M16": 500, "M20": 830,
    "M24": 1270, "M30": 2600, "M36": 3700, "M42": 5000, "M48": 6100, "M56": 8300
}

# Material line (as on your sheet)
MATERIALS = {
    "C15": {"tensile": 540.0, "yield": 295.0, "allowable": 295.0 / 4.0},  # 73.75 MPa
}

def render_dc012():
    st.markdown("<h2 style='text-align:center;margin:0;'>LIFTING LUGS CALCULATION</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC012</h4>", unsafe_allow_html=True)
    st.markdown("### LIFTING EYE BOLTS")

    # Defaults
    P_default = float(st.session_state.get("valve_weight_kg", 41.0))

    # ---- Inputs (left block like your sheet) ----
    c1, c2 = st.columns([1.2, 1.2])
    with c1:
        P_kg = st.number_input("Valve weight P [kg] =", value=P_default, step=0.1, format="%.2f")

        thread = st.selectbox("Eye bolt thread =", THREADS, index=THREADS.index("M10"))
        # auto-fill A from table but allow override
        A_mm2 = st.number_input("Cross sectional area A [mm²] =", value=float(AREA_MAP[thread]), step=1.0, format="%.0f")

        N = st.number_input("Quantity of eye bolt N =", value=4, step=1, min_value=1)

        angle = st.radio("Lifting angle", ["0° (straight)", "45°"], index=0, horizontal=True)
        rated_tbl = RATED_0_MAP if "0°" in angle else RATED_45_MAP
        F_rated_kg_default = rated_tbl.get(thread)

        # Show table default; allow override
        if F_rated_kg_default is None:
            st.info("Rated load for this size at selected angle not in the sheet. Enter a value manually.")
            F_rated_kg_default = 0.0
        F_rated_kg = st.number_input("Force eye bolt F [kg] – (UNI-ISO 3266) =", value=float(F_rated_kg_default),
                                     step=1.0, format="%.0f")

    with c2:
        # Display the side table like the sheet
        df = pd.DataFrame({
            "Thread": THREADS,
            "Area A [mm²]": [AREA_MAP[t] for t in THREADS],
            "Rated 0° [kg]": [RATED_0_MAP[t] if RATED_0_MAP[t] is not None else "" for t in THREADS],
            "Rated 45° [kg]": [RATED_45_MAP[t] for t in THREADS],
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ---- Checks & calculations ----
    # 1) Eye bolt stress condition Ec (UNI-ISO 3266): per-bolt weight ≤ rated load
    per_bolt_kg = P_kg / N
    ec_ok = per_bolt_kg <= F_rated_kg if F_rated_kg > 0 else False

    # 2) Effective eye bolt stress Es [MPa] = (P * g) / (N * A)
    g = 9.81  # m/s²
    Es_MPa = (P_kg * g) / (N * A_mm2) if (N > 0 and A_mm2 > 0) else float("nan")

    st.markdown("### EYE BOLT STRESS CONDITION Ec (UNI-ISO 3266)")
    st.text_input("Ec result", value=("OK" if ec_ok else "NOT OK"), disabled=True)

    st.markdown("### EFFECTIVE EYE BOLT STRESS CALCULATION Es")
    st.text_input("Es [MPa]", value=f"{Es_MPa:.2f}" if Es_MPa == Es_MPa else "—", disabled=True)

    # Material check row (as in your sheet)
    mat_name = st.selectbox("MATERIAL", list(MATERIALS.keys()), index=0)
    mat = MATERIALS[mat_name]
    m1, m2, m3, m4, m5 = st.columns([1, 1, 1, 1, 1])
    with m1: st.text_input("TENSILE [MPa]", value=f"{mat['tensile']:.0f}", disabled=True)
    with m2: st.text_input("YIELD [MPa]", value=f"{mat['yield']:.0f}", disabled=True)
    with m3: st.text_input("ALL. [MPa]", value=f"{mat['allowable']:.2f}", disabled=True)
    with m4: st.text_input("Es [MPa] (again)", value=f"{Es_MPa:.2f}" if Es_MPa == Es_MPa else "—", disabled=True)
    with m5:
        stress_ok = (Es_MPa == Es_MPa) and (Es_MPa <= mat["allowable"])
        st.text_input("Result", value=("OK" if stress_ok else "NOT OK"), disabled=True)

    # Save for reports/export
    st.session_state["dc012"] = {
        "P_kg": float(P_kg),
        "thread": thread,
        "A_mm2": float(A_mm2),
        "N": int(N),
        "angle": angle,
        "F_rated_kg": float(F_rated_kg),
        "Ec_ok": bool(ec_ok),
        "Es_MPa": float(Es_MPa) if Es_MPa == Es_MPa else None,
        "material": mat_name,
        "allowable_MPa": float(mat["allowable"]),
        "stress_ok": bool(stress_ok),
    }
