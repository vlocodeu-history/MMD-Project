# page_dc011.py
import math
import pandas as pd
import streamlit as st

# Friction factor table (from your sheet)
FT_TABLE = [
    (0.50, 0.027), (0.75, 0.025), (1.00, 0.023), (1.25, 0.022),
    (1.50, 0.021), (2.00, 0.019), (2.50, 0.018), (3.00, 0.018),
    (4.00, 0.017), (5.00, 0.016), (6.00, 0.015), (8.00, 0.014),
    (10.0, 0.014), (12.0, 0.013), (14.0, 0.013), (16.0, 0.013),
    (18.0, 0.012), (20.0, 0.012),
]
DN_OPTIONS = [dn for dn, _ in FT_TABLE]
FT_MAP = dict(FT_TABLE)

def _default_bore_mm():
    # try to pick from earlier pages
    return float(st.session_state.get("bore_diameter_mm", 51.0))

def render_dc011():
    """
    DC011 — FLOW COEFFICIENT Cv CALCULATION

    Model used (matches your sheet example):
      - Local resistance coefficient K_local:
          * If θ = 0 → use K1 (default 0.057)  [straight bore / no taper]
          * If θ > 0 → use K2 (default 0.057)  [tapered seat option]
      - Optional distributed loss due to friction in taper length:
          K_fric = f_t · (L / D)
      - Total K = K_local + K_fric
      - Cv relation to K (water, 1 psi base):  Cv = 29.9 · d_in^2 / sqrt(K)
        (d_in in inches). With D = 2 in and K = 0.057 → Cv ≈ 505 (sheet value).

    Notes:
      * Bore ratio β = SeatBore / InnerBore (shown for reference).
      * θ (deg) shown, radians computed.
      * If θ = 0, taper length is treated as N.A. (ignored).
    """

    st.markdown("<h2 style='text-align:center;margin:0;'>FLOW COEFFICIENT CV CALCULATION</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC011</h4>", unsafe_allow_html=True)
    st.markdown("### FLOW COEFFICIENT CV CALCULATION")

    # Left grid (inputs like sheet)
    c1, c2 = st.columns([1.2, 1.2])
    with c1:
        inner_bore_mm = st.number_input("Inner Bore [mm] =", value=_default_bore_mm(), step=0.1, format="%.2f")
        seat_bore_mm  = st.number_input("Seat Bore [mm] =", value=round(_default_bore_mm(), 2), step=0.01, format="%.2f")
        beta = seat_bore_mm / inner_bore_mm if inner_bore_mm > 0 else float("nan")
        st.text_input("Bore ratio β =", value=f"{beta:.3f}", disabled=True)

        theta_deg = st.number_input("Tapering angle θ [degree] =", value=0.0, step=0.1, format="%.1f")
        theta_rad = math.radians(theta_deg)
        st.text_input("Tapering angle θ [radians] =", value=f"{theta_rad:.6f}", disabled=True)

        # If θ==0, treat taper length as N.A. (we still keep an input but ignore it)
        taper_len_mm = 0.0
        if theta_deg > 0:
            taper_len_mm = st.number_input("Tapering length L [mm] =", value=0.0, step=0.1, format="%.1f")
        else:
            st.text_input("Tapering length [mm] =", value="N.A.", disabled=True)

        # Friction factor from table (DN dropdown on the right of the sheet)
        dn_default = float(st.session_state.get("valve_nps", 2))
        dn_choice = st.selectbox("DN (for friction factor fₜ)", DN_OPTIONS,
                                 index=DN_OPTIONS.index(dn_default) if dn_default in DN_OPTIONS else DN_OPTIONS.index(2.00))
        ft = FT_MAP[dn_choice]
        st.text_input("Friction factor fₜ =", value=f"{ft:.3f}", disabled=True)

        # Resistance coefficients (kept explicit as in sheet; default 0.057)
        K1 = st.number_input("Resistance coefficient K1", value=0.057, step=0.001, format="%.3f")
        K2 = st.number_input("Resistance coefficient K2", value=0.057, step=0.001, format="%.3f")

    with c2:
        # Show the FT table (like the side table in the sheet)
        df = pd.DataFrame(FT_TABLE, columns=["DN (in)", "fₜ"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Compute total resistance coefficient K ---
    D_mm = inner_bore_mm
    D_in = inner_bore_mm / 25.4 if inner_bore_mm > 0 else float("nan")

    K_local = K1 if theta_deg == 0 else K2
    K_fric = 0.0
    if theta_deg > 0 and taper_len_mm > 0 and inner_bore_mm > 0:
        K_fric = ft * (taper_len_mm / inner_bore_mm)  # dimensionless

    K_total = K_local + K_fric

    # Cv at ΔP = 1 psi for water (SG=1): Cv = 29.9 * d_in^2 / sqrt(K)
    if K_total > 0 and D_in > 0:
        Cv = 29.9 * (D_in ** 2) / math.sqrt(K_total)
    else:
        Cv = float("nan")

    st.markdown("----")
    st.text_input("Flow coefficient **Cv** (gpm @ 1 psi)", value=f"{Cv:,.0f}" if Cv == Cv else "—", disabled=True)

    # Save to session for other pages/reports
    st.session_state["dc011"] = {
        "inner_bore_mm": float(inner_bore_mm),
        "seat_bore_mm": float(seat_bore_mm),
        "beta": float(beta),
        "theta_deg": float(theta_deg),
        "theta_rad": float(theta_rad),
        "taper_len_mm": float(taper_len_mm),
        "dn_choice_in": float(dn_choice),
        "ft": float(ft),
        "K1": float(K1),
        "K2": float(K2),
        "K_local": float(K_local),
        "K_fric": float(K_fric),
        "K_total": float(K_total),
        "Cv_gpm_at_1psi": float(Cv) if Cv == Cv else None,
    }
