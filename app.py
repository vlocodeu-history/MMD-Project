# app.py
import streamlit as st
import importlib
from auth import login_form, register_form, validate_token, logout_now  # updated helpers

st.set_page_config(page_title="Valve Design Suite", layout="wide")

# --- safe imports with helpful messages ---
missing_modules = []
def safe_import(mod_name, func_name):
    try:
        mod = importlib.import_module(mod_name)
        if not hasattr(mod, func_name):
            return None, (mod_name, f"does not define `{func_name}()`")
        return mod, None
    except Exception as e:
        return None, (mod_name, str(e))

pv, err1  = safe_import("page_valve",  "render_valve")
pd, err2  = safe_import("page_dc001",  "render_dc001")
pa, err3  = safe_import("page_dc001a", "render_dc001a")
ps, err4  = safe_import("page_dc002",  "render_dc002")
pc, err5  = safe_import("page_dc002a", "render_dc002a")
pe, err6  = safe_import("page_dc003",  "render_dc003")
pf, err7  = safe_import("page_dc004",  "render_dc004")
pg, err8  = safe_import("page_dc005",  "render_dc005")
ph, err9  = safe_import("page_dc005a", "render_dc005a")
pi, err10 = safe_import("page_dc006",  "render_dc006")
pj, err11 = safe_import("page_dc006a", "render_dc006a")
pk, err12 = safe_import("page_dc007_body",        "render_dc007_body")
pl, err13 = safe_import("page_dc007_body_holes",  "render_dc007_body_holes")
pm, err14 = safe_import("page_dc008",  "render_dc008")
pn, err15 = safe_import("page_dc010",  "render_dc010")
po, err16 = safe_import("page_dc011",  "render_dc011")
pp, err17 = safe_import("page_dc012",  "render_dc012")

for err in (err1, err2, err3, err4, err5, err6, err7, err8, err9, err10, err11, err12, err13, err14, err15, err16, err17):
    if err:
        missing_modules.append(err)

if missing_modules:
    st.error("One or more page modules failed to import. See details below.")
    for name, msg in missing_modules:
        st.markdown(f"**{name}**: `{msg}`")
    st.stop()

# --- PAGE MAP ---
PAGE_MAP = {
    "Valve Data": pv.render_valve,
    "DC001 (Seat insert & spring)": pd.render_dc001,
    "DC001A (Self relieving)": pa.render_dc001a,
    "DC002 (Body-closure bolts)": ps.render_dc002,
    "DC002A (Bolts test condition)": pc.render_dc002a,
    "DC003 (Bearing stress)": pe.render_dc003,
    "DC004 (Seat thickness)": pf.render_dc004,
    "DC005 (Bolt calc – gland)": pg.render_dc005,
    "DC005A (Bolt calc – test)": ph.render_dc005a,
    "DC006 (Flange stress)": pi.render_dc006,
    "DC006A (Flange stress – test)": pj.render_dc006a,
    "DC007_1_body (Body wall thickness)": pk.render_dc007_body,
    "DC007-2_body (Body holes)": pl.render_dc007_body_holes,
    "DC008 (Ball sizing)": pm.render_dc008,
    "DC010 (Valve Torque Calculation)": pn.render_dc010,
    "DC011 (Flow Coefficient (Cv) Calculation)": po.render_dc011,
    "DC012 (Lifting Lugs (Eye Bolts) Calculation)": pp.render_dc012,
}

# ---- state ----
if "active_page" not in st.session_state:
    st.session_state.active_page = "Valve Data"
if "auth_view" not in st.session_state:
    st.session_state.auth_view = None  # None | "login" | "register"

# ---------- AUTO-LOGIN VIA URL TOKEN (persists across hard refresh) ----------
if "user" not in st.session_state:
    token = st.query_params.get("auth")
    if isinstance(token, list):
        token = token[0] if token else None
    v = validate_token(token)
    if v:
        st.session_state["user"] = {
            "username": v["username"],
            "role": v["role"],
            "first_name": v.get("first_name", ""),
            "last_name": v.get("last_name", ""),
        }
        if st.session_state.get("auth_view") in ("login", None):
            st.session_state["active_page"] = "Valve Data"
            st.session_state["auth_view"] = None

# ---- CSS ----
SIDEBAR_WIDTH = 280
st.markdown(
    f"""
<style>
/* Sidebar fixed width (no toggle) */
section[data-testid="stSidebar"] {{ width:{SIDEBAR_WIDTH}px !important; }}
div[data-testid="stSidebar"] > div:first-child {{ width:{SIDEBAR_WIDTH}px !important; }}
section[data-testid="stSidebar"] > div:first-child {{
  height: 100vh; overflow-y: auto; overflow-x: hidden;
  border-right: 1px solid #e5e7eb; background:#f8fafc; padding-bottom: 6rem;
}}
div.block-container {{ padding-top: 0.5rem; }}

/* Profile card at top of sidebar */
.sidebar-profile {{
  padding: .5rem .5rem .75rem .5rem; margin-bottom:.5rem; border-bottom:1px solid #e5e7eb;
  background:#ffffff; border-radius:.5rem;
}}
.sidebar-profile .name {{ font-weight:700; }}
.sidebar-profile .role {{ font-size:.85rem; color:#475569; }}

/* Sticky auth footer */
.sidebar-auth-footer {{
  position: sticky; bottom: 0; left: 0; right: 0;
  padding: .5rem .25rem .75rem .25rem;
  background: linear-gradient(180deg, rgba(248,250,252,0) 0%, rgba(248,250,252,1) 30%);
  border-top: 1px solid #e5e7eb;
}}
.sidebar-auth-footer .btn-signin button    {{ background:#3b82f6 !important; color:#fff !important; border-color:#3b82f6 !important; }}
.sidebar-auth-footer .btn-register button  {{ background:#22c55e !important; color:#fff !important; border-color:#22c55e !important; }}
.sidebar-auth-footer .btn-logout button    {{ background:#ef4444 !important; color:#fff !important; border-color:#ef4444 !important; }}
.sidebar-auth-footer button:hover {{ filter:brightness(0.95); }}
</style>
""",
    unsafe_allow_html=True,
)

# ---- NAVBAR (sidebar) ----
with st.sidebar:
    # Profile header (instead of toggle)
    user = st.session_state.get("user")
    if user:
        full_name = f"{user.get('first_name','').strip()} {user.get('last_name','').strip()}".strip()
        display_name = full_name if full_name else user.get("username", "")
        st.markdown(
            f"""
            <div class="sidebar-profile">
                <div class="name">{display_name}</div>
                <div class="role">{user.get('role','user').title()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="sidebar-profile">
                <div class="name">Welcome</div>
                <div class="role">Please sign in</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Pages
    pages_full = list(PAGE_MAP.keys())
    try:
        current_index = pages_full.index(st.session_state.active_page)
    except ValueError:
        current_index = 0

    st.markdown("### Valve Design Suite")
    choice = st.radio("Pages", pages_full, index=current_index)
    st.session_state.active_page = choice

    # Auth footer buttons
    st.markdown('<div class="sidebar-auth-footer">', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")

    if user:
        with c1:
            st.markdown('<div class="btn-logout">', unsafe_allow_html=True)
            if st.button("Logout", use_container_width=True):
                logout_now()
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            if user.get("role") == "superadmin":
                st.markdown('<div class="btn-register">', unsafe_allow_html=True)
                if st.button("Register", use_container_width=True):
                    st.session_state.auth_view = "register"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.empty()
    else:
        with c1:
            st.markdown('<div class="btn-signin">', unsafe_allow_html=True)
            if st.button("Sign in", use_container_width=True):
                st.session_state.auth_view = "login"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.empty()

    st.markdown("</div>", unsafe_allow_html=True)  # /sidebar-auth-footer

# ---- MAIN ----
# Only redirect away from the login form if already logged in.
if st.session_state.get("user") and st.session_state.get("auth_view") == "login":
    st.session_state["auth_view"] = None
    st.session_state["active_page"] = "Valve Data"
    st.rerun()

if st.session_state.auth_view == "login":
    st.title("Login")
    st.markdown("---")
    login_form()
elif st.session_state.auth_view == "register":
    st.title("Register (superadmin only)")
    st.markdown("---")
    register_form()
else:
    if not st.session_state.get("user"):
        st.title("Please sign in")
        st.markdown("---")
        st.warning("You must **sign in** to access the calculation pages.")
        if st.button("Open Sign in form"):
            st.session_state.auth_view = "login"
            st.rerun()
    else:
        st.title(st.session_state.active_page)
        st.markdown("---")
        try:
            PAGE_MAP[st.session_state.active_page]()
        except Exception as e:
            st.error(f"Error while rendering {st.session_state.active_page}: {e}")
