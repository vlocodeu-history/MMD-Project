# page_dc007_body.py
import os
from PIL import Image
import streamlit as st

# --- ASME B16.34 Table lookup (minimal set; includes your case) ---
# Table 3A & Table VI-1 -> minimum body wall thickness t_m [mm]
B1634_TMIN = {
    (2, 600): 12.7,   # your sheet value
    # add more as needed, e.g. (2,150): x, (2,300): y, etc.
}

def _img_dc007(size_px: int = 300):
    for p in ["dc007_body.png", "assets/dc007_body.png", "static/dc007_body.png"]:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
                st.image(img, caption="Fig. 2 ASME B16.34 (body section)", use_column_width=False)
            except Exception as e:
                st.warning(f"Could not load DC007 body diagram ({e}).")
            return
    st.info("Add **dc007_body.png** (or put it in ./assets/ or ./static/) to show the figure here.")

def render_dc007_body():
    """
    DC007-1 — Body Wall Thickness Calc. per ASME B16.34 (Body)

    Matches sheet fields:
      Inputs: ASME class, Pa, temperature range, C/A; material; diameters; actual thicknesses.
      Calculations:
        d (inside diameter) = body inside diameter
        t_m  (from ASME B16.34 tables)  -> for NPS 2, Class 600 = 12.7 mm
        t_m+CA = t_m + C/A
      Checks:
        body t ≥ t_m             (per B16.34 §6.1.2 / Fig.2)
        body/t ≥ t_m             (same criterion used on sheet)
    """
    st.markdown("<h2 style='text-align:center;margin:0;'>Body Wall Thickness Calc. in acc. With ASME B16.34</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;margin:0;'>DC 007-1-(Body)</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Header (pull NPS & class if available)
    nps_default   = int(st.session_state.get("valve_nps", 2))  # 2 in
    class_default = int(st.session_state.get("valve_asme_class", 600))
    Pa_default    = float(st.session_state.get("operating_pressure_mpa", 10.21))

    head1, head2, head3, head4 = st.columns([1,1,1,1])
    with head1:
        nps = st.number_input("Class rating — NPS [in]", value=nps_default, step=1)
    with head2:
        asme_class = st.number_input("ASME (Valve Class)", value=class_default, step=50)
    with head3:
        Pa = st.number_input("Design pressure Pa [MPa]", value=Pa_default, step=0.01, format="%.2f")
    with head4:
        st.text_input("Design temperature T [°C]", value="-29 / +150", disabled=False)

    head5, head6 = st.columns([1,1])
    with head5:
        CA = st.number_input("Corrosion allowance C/A [mm]", value=3.0, step=0.1, format="%.1f")
    with head6:
        material = st.text_input("Material", value="ASTM A350 LF2 CL.1")

    st.markdown("### BODY  (as per ASME B16.34 – Ed.2020)")

    # Dimensions (green inputs in sheet)
    dim1, dim2, dim3 = st.columns([1,1,1])
    with dim1:
        body_ID = st.number_input("Body inside diameter [mm]", value=98.0, step=0.1, format="%.1f")
    with dim2:
        flow_pass_d = st.number_input("Diameter of the flow passage [mm]", value=51.0, step=0.1, format="%.1f")
    with dim3:
        end_flange_ID = st.number_input("Inside diameter at the end flange [mm]", value=51.0, step=0.1, format="%.1f")

    d = body_ID  # per sheet: printed again as 'inside diameter d ='
    st.text_input("inside diameter  d =", value=f"{d:.1f} mm", disabled=True)

    # Actual thickness inputs (green)
    thick1, thick2 = st.columns([1,1])
    with thick1:
        t_body = st.number_input("actual thickness — body t [mm]", value=43.5, step=0.1, format="%.1f")
    with thick2:
        t_body_top = st.number_input("actual thickness on top mill — body/t [mm]", value=34.0, step=0.1, format="%.1f")

    # Table lookup for minimum wall thickness
    t_m = B1634_TMIN.get((int(nps), int(asme_class)))
    if t_m is None:
        # If combination not in our small table, show a note and use the sheet's value as a conservative placeholder.
        st.warning("ASME B16.34 table value for this NPS/Class not in local map; using 12.7 mm as placeholder. Extend B1634_TMIN as required.")
        t_m = 12.7

    t_m_ca = t_m + CA

    calc1, calc2 = st.columns([1,1])
    with calc1:
        st.text_input("min wall thickness  tₘ  [mm]  (ASME B16.34 §6.1.1 · Table 3A / VI-1)", value=f"{t_m:.1f}", disabled=True)
    with calc2:
        st.text_input("min wall thickness + C/A (3 mm)  tₘ + C/A  [mm]", value=f"{t_m_ca:.1f}", disabled=True)

    # Checks (sheet annotates ≥ t_m next to the two actual-thickness lines)
    ok1 = t_body >= t_m
    ok2 = t_body_top >= t_m
    ok_ca1 = t_body >= t_m_ca
    ok_ca2 = t_body_top >= t_m_ca

    st.markdown(
        f"""
<div style="display:flex;gap:1rem;align-items:center;">
  <div>Check (body t ≥ tₘ): <b style="color:{'#16a34a' if ok1 else '#dc2626'}">{'OK' if ok1 else 'NOT OK'}</b></div>
  <div>Check (body/t ≥ tₘ): <b style="color:{'#16a34a' if ok2 else '#dc2626'}">{'OK' if ok2 else 'NOT OK'}</b></div>
</div>
<div style="display:flex;gap:1rem;align-items:center;margin-top:.25rem;">
  <div>Check incl. C/A (body t ≥ tₘ + C/A): <b style="color:{'#16a34a' if ok_ca1 else '#dc2626'}">{'OK' if ok_ca1 else 'NOT OK'}</b></div>
  <div>Check incl. C/A (body/t ≥ tₘ + C/A): <b style="color:{'#16a34a' if ok_ca2 else '#dc2626'}">{'OK' if ok_ca2 else 'NOT OK'}</b></div>
</div>
""",
        unsafe_allow_html=True
    )

    _img_dc007(300)

    # Persist to session (useful elsewhere)
    st.session_state["dc007_body"] = {
        "nps_in": int(nps),
        "asme_class": int(asme_class),
        "Pa_MPa": float(Pa),
        "CA_mm": float(CA),
        "material": material,
        "body_ID_mm": float(body_ID),
        "flow_pass_d_mm": float(flow_pass_d),
        "end_flange_ID_mm": float(end_flange_ID),
        "t_body_mm": float(t_body),
        "t_body_top_mm": float(t_body_top),
        "t_m_mm": float(t_m),
        "t_m_plus_CA_mm": float(t_m_ca),
        "ok_body_vs_tm": ok1,
        "ok_top_vs_tm": ok2,
        "ok_body_vs_tmCA": ok_ca1,
        "ok_top_vs_tmCA": ok_ca2,
    }
