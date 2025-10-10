import math
import streamlit as st

def render_dc001():
    """
    DC001 — Seat insert & spring calculation (matches your sheet)

    - Spring load calc: Fm = π * Dm * q * z
    - Nº of springs calc (exactly like your image):
        P (input), Nm = Fm/P, f (input),
        Pr = P * (f - 0.5) / f,
        Nmr = Fm / Pr,
        Nma (default ceil(Nmr), editable)
    - SPRING CHECK:
        Total load of springs = Pr
        C1effective = Pr / (π * Dm)
        VERIFIED if Pr >= Fm else NOT VERIFIED
    - SEAT INSERT MATERIAL: unchanged (same as older section)
    - Seat Insert validation (your formulas):
        Dcs = Di + ((De - Di)/2)/3 * 2  = (De + 2*Di)/3
        Dc (input), Pa (input MPa)
        F = (Dc^2 - ((De + Di)/2)^2) * 1.1 * Pa * π/4 + Fmr, with Fmr = Pr
        Q = F * 4 / ((De^2 - Di^2) * π)
        Check Q < Y_max
    """

    # ───────── Header ─────────
    st.markdown("<h2 style='margin:0;text-align:center;'>Seat insert and spring calculation</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin:0;text-align:center;'>DC001</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # ───────── A) Spring load calculation ─────────
    st.subheader("Spring load calculation")

    c1, c2, c3, c4 = st.columns([3,2,2,3])
    with c1:
        Dm = st.number_input(
            "Seat insert medium dia. (Ball/seat seal diameter)  Dm",
            value=round(float(st.session_state.get("bore_diameter_mm", 62.3)), 3),
            step=0.1, format="%.3f", help="[mm]"
        )
    with c2:
        q = st.number_input("Load ' length unit'  q", value=2.5, step=0.1, format="%.2f", help="[N/mm]")
    with c3:
        z = st.number_input("Correction factor  z", value=1.0, step=0.01, format="%.2f")
    with c4:
        Fm = float(math.pi * Dm * q * z)  # [N]
        st.text_input("Theoric load spring  Fm", value=f"{Fm:.6f}", disabled=True, help="[N]")

    st.markdown("")

    # ───────── B) N° of springs calculation (exactly like your image) ─────────
    st.subheader("N° of springs calculation")

    n1, n2, n3, n4, n5, n6 = st.columns([2,2,2,2,2,2])

    with n1:
        P = st.number_input("Load at theoric packing  P", value=1020.0, step=1.0, format="%.3f", help="[N]")

    with n2:
        Nm = float(Fm / max(P, 1e-9))               # Fmt / P = Nm
        st.text_input("N° of springs request  Fmt / P = Nm", value=f"{Nm:.8f}", disabled=True)

    with n3:
        f = st.number_input("Theoric spring arrow  f", value=2.19, step=0.01, format="%.2f", help="[mm]")

    with n4:
        Pr = float(P * (f - 0.5) / max(f, 1e-9))    # Load at real packing
        st.text_input("Load at real packing  P × (f-0.5) / f = Pr", value=f"{Pr:.6f}", disabled=True, help="[N]")

    with n5:
        Nmr = float(Fm / max(Pr, 1e-9))             # N° of springs real
        st.text_input("N° of springs real  Fmt / Pr = Nmr", value=f"{Nmr:.8f}", disabled=True)

    with n6:
        Nma_default = max(1, int(math.ceil(Nmr)))
        Nma = st.number_input("N° of springs in the project  Nma", value=Nma_default, step=1, min_value=1)

    st.markdown("")

    # ───────── C) SPRING CHECK ─────────
    st.subheader("SPRING CHECK")

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        total_load = Pr                              # per your sheet, equals the value shown
        st.text_input("Total load of springs  =", value=f"{total_load:.6f}", disabled=True, help="[N]")
    with sc2:
        C1effective = float(total_load / (math.pi * max(Dm, 1e-9)))   # [N/mm]
        st.text_input("C1effective  Fr /(π × Dm) =", value=f"{C1effective:.6f}", disabled=True, help="[N/mm]")
    with sc3:
        check_str = "VERIFIED" if total_load >= Fm else "NOT VERIFIED"
        st.text_input("Check", value=check_str, disabled=True)

    st.markdown("")

    # ───────── D) SEAT INSERT MATERIAL — (unchanged, same as your older code) ─────────
    st.subheader("SEAT INSERT MATERIAL")
    st.markdown("Y = Max. Seat Insert Stress")

    materials = [
        ("PTFE", 9),
        ("PTFE Reinforced", 12),
        ("NYLON 12 G", 60),
        ("PCTFE (KELF)", 60),
        ("PEEK", 90),
        ("DELVON V", 60),
    ]
    mat_choice = st.selectbox("Material", options=[m[0] for m in materials], index=0)
    Y_max = float(dict(materials)[mat_choice])
    st.text_input("Y_max [MPa] (value from catalogue manufacturer)", value=f"{Y_max:.3f}", disabled=True)

    st.markdown("")

    # ───────── E) Seat Insert validation (your formulas) ─────────
    st.subheader("Seat Insert validation")

    v1, v2, v3, v4 = st.columns(4)
    with v1:
        De = st.number_input("External seat insert diameter  De", value=66.74, step=0.01, format="%.2f", help="[mm]")
    with v2:
        Di = st.number_input("Internal seat insert diameter  Di", value=57.86, step=0.01, format="%.2f", help="[mm]")
    with v3:
        # Dcs = Di + ((De - Di)/2)/3 * 2  -> simplifies to (De + 2*Di) / 3
        Dcs = (De + 2.0 * Di) / 3.0
        st.text_input("Seat insert medium dia. (Ball/seat seal diameter)  Dcs", value=f"{Dcs:.3f}", disabled=True)
    with v4:
        Dc = st.number_input("Seat/Closure seal diameter  Dc", value=round(Dm, 3), step=0.01, format="%.2f", help="[mm]")

    v5, v6, v7, v8 = st.columns(4)
    with v5:
        Pa = st.number_input("Rating pressure  Pa", value=float(st.session_state.get("operating_pressure_mpa", 10.21)),
                              step=0.01, format="%.2f", help="[MPa]")
    with v6:
        # Fmr = total spring load from spring check = Pr
        Fmr = total_load
        # Pressure resultant on ring area between Dc and (De+Di)/2, with 1.1 factor
        DeDi_mean = (De + Di) / 2.0
        pressure_term = (Dc**2 - DeDi_mean**2) * 1.1 * Pa * (math.pi / 4.0)   # N  (MPa * mm^2 = N)
        F = pressure_term + Fmr
        st.text_input("Linear Load  (Dc² - ((De+Di)/2)²) × 1.1 × Pa × π/4 + Fmr  =  F", value=f"{F:.6f}", disabled=True)
    with v7:
        denom_area = max((De**2 - Di**2) * math.pi, 1e-9)                      # mm² * π
        Q = F * 4.0 / denom_area                                               # MPa (N/mm²)
        st.text_input("Insert resistance  Q = F × 4 / ((De² - Di²) × π)", value=f"{Q:.6f}", disabled=True)
    with v8:
        result = "OK (Q < Y_max)" if Q < Y_max else "NOT OK (Q ≥ Y_max)"
        st.text_input("Q < Y Mpa (value by manufacturer Seat Insert Material Data Sheet)", value=result, disabled=True)

    # (Optional) stash
    st.session_state["dc001"] = {
        "P": P, "Nm": Nm, "f": f, "Pr": Pr, "Nmr": Nmr, "Nma": int(Nma),
        "Dm": Dm, "C1effective": C1effective, "check": check_str,
        "De": De, "Di": Di, "Dcs": Dcs, "Dc": Dc, "Pa": Pa,
        "F": F, "Q": Q, "Y_max": Y_max, "Q_check": result
    }
