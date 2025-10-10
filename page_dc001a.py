import math, os
import streamlit as st
from PIL import Image

K_FACTOR = 1.33  # per sheet: 1.33 × Po × π/4 × (Dts² − Dc²)

def _try_show_diagram(size_px: int = 500):
    """
    Render the DC001A diagram at a fixed square size (default 300x300 px).
    Increase `size_px` when calling this function to make it bigger (e.g., 500).
    """
    paths = ["dc001a_diagram.png", "assets/dc001a_diagram.png", "static/dc001a_diagram.png"]
    for p in paths:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA")
                img = img.resize((size_px, size_px), Image.LANCZOS)  # exact WxH
                st.image(img, caption="Self-relieving seat sketch", use_column_width=False)
            except Exception as e:
                st.warning(f"Couldn't load diagram ({e}).")
            return
    st.info("Add an image named **dc001a_diagram.png** (or put it in ./assets/ or ./static/) to display the sheet diagram here.")
    
def render_dc001a():
    """
    DC001A — SELF RELIEVING CALCULATION (SR)
    SR = 1.33 × Po [N/mm²] × (π/4) × (Dts² − Dc²) ≥ F_molle [N]
    Links:
      Po  <- Valve Data (operating_pressure_mpa) if present
      Dc  <- Valve Data (bore_diameter_mm) if present
      F_molle <- DC001.Pr (load at real packing) if present
    """

    # ── Header block (DN / Class / Tag / Rev) ──────────────────────────────────────
    nps = st.session_state.get("valve_nps", None)
    asme_class = st.session_state.get("valve_asme_class", 600)
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 0.6])
    with c1:
        dn_display = f'{nps}"' if nps else ""
        dn_display = st.text_input("Valve DN", value=dn_display)
    with c2:
        st.text_input("Class", value=str(asme_class), disabled=True)
    with c3:
        tag_no = st.text_input("Tag no", value=st.session_state.get("tag_no", ""))
        st.session_state["tag_no"] = tag_no
    with c4:
        rev = st.number_input("Rev.", value=int(st.session_state.get("rev_no", 0)), step=1, format="%d")
        st.session_state["rev_no"] = rev

    st.markdown("<h3 style='text-align:center;margin:.5rem 0;'>SELF RELIEVING CALCULATION (SR)</h3>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Inputs (right-side yellow cells in your sheet) ─────────────────────────────
    Po_default = float(st.session_state.get("operating_pressure_mpa", 10.21))
    c5, c6 = st.columns([1.2, 1])
    with c5:
        st.text_input("Valve class =", value=str(asme_class), disabled=True)
    with c6:
        Po = st.number_input("Operating pressure Po [MPa] =", value=Po_default, step=0.01, format="%.2f")

    # ── Diagram (image) ────────────────────────────────────────────────────────────
    _try_show_diagram()

    st.markdown("---")

    # ── Geometry & force inputs (yellow cells at the bottom bar) ───────────────────
    Dc_default = float(st.session_state.get("bore_diameter_mm", 62.3))
    dc_col, dts_col, fm_col = st.columns([1.2, 1.2, 1.2])
    with dc_col:
        Dc = st.number_input("ØDc (seat/closure diameter) [mm]", value=round(Dc_default, 1), step=0.1, format="%.1f")
    with dts_col:
        Dts = st.number_input("ØDts (relieving seat diameter) [mm]", value=71.0, step=0.1, format="%.1f")
    with fm_col:
        # default F_molle from DC001 (Pr)
        pr_from_dc001 = None
        dc001_state = st.session_state.get("dc001")
        if isinstance(dc001_state, dict):
            pr_from_dc001 = dc001_state.get("Pr", None)
        F_molle = st.number_input("F_molle (spring force) [N]", value=float(pr_from_dc001 or 787.1), step=0.1, format="%.1f")

    # ── Core calculation (show intermediate area explicitly) ───────────────────────
    # A = π/4 × (Dts² − Dc²)   [mm²]
    A = (math.pi / 4.0) * (Dts**2 - Dc**2)
    # Po is MPa = N/mm², so SR is in N
    SR = K_FACTOR * Po * A

    # Results row styled like the sheet
    r1, r2, r3 = st.columns([1.6, 1.2, 1.2])
    with r1:
        st.text_input("SR =", value=f"{SR:,.2f}", disabled=True)
    with r2:
        st.text_input("≥  F_molle =", value=f"{F_molle:,.1f}", disabled=True)
    with r3:
        verdict = "VERIFIED" if SR >= F_molle else "NOT VERIFIED"
        st.text_input("", value=verdict, disabled=True)

    # Debug/trace (helps validate numbers if something looks off)
    with st.expander("Show intermediate values"):
        st.write({
            "K_FACTOR": K_FACTOR,
            "Po [MPa=N/mm²]": Po,
            "Dc [mm]": Dc,
            "Dts [mm]": Dts,
            "A = π/4·(Dts²−Dc²) [mm²]": A,
            "SR [N]": SR,
            "F_molle [N]": F_molle
        })

    st.markdown("---")
    st.markdown("*Self relieving at* **0.4 MPa**")

    # save for downstream
    st.session_state["dc001a"] = {
        "DN": dn_display, "class": asme_class, "tag_no": tag_no, "rev": rev,
        "Po_MPa": Po, "Dc_mm": Dc, "Dts_mm": Dts, "F_molle_N": F_molle,
        "A_mm2": A, "SR_N": SR, "verdict": verdict
    }
