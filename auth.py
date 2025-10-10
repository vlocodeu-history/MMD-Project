# auth.py
import json, os, time, hashlib, secrets
import streamlit as st

USERS_FILE  = "users.json"
TOKENS_FILE = "tokens.json"   # token -> {username, role, first_name, last_name, exp, created_at}

DEFAULT_SUPERADMIN = {
    "username": "superadmin",
    "password": "Super@123",   # will be hashed on first run
    "role": "superadmin",
    "first_name": "Super",
    "last_name": "Admin",
}

# ----------------- low-level stores -----------------
def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def _ensure_store():
    """Create users.json (and tokens.json) with default superadmin if they don't exist."""
    if not os.path.exists(USERS_FILE):
        salt = secrets.token_hex(16)
        users = {
            DEFAULT_SUPERADMIN["username"]: {
                "salt": salt,
                "pwd": _hash_password(DEFAULT_SUPERADMIN["password"], salt),
                "role": DEFAULT_SUPERADMIN["role"],
                "first_name": DEFAULT_SUPERADMIN["first_name"],
                "last_name": DEFAULT_SUPERADMIN["last_name"],
                "created_at": int(time.time()),
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
    if not os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def _load_users() -> dict:
    _ensure_store()
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def _load_tokens() -> dict:
    _ensure_store()
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_tokens(tokens: dict):
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)

def _get_user_record(username: str) -> dict | None:
    return _load_users().get(username)

# ----------------- auth core -----------------
def authenticate(username: str, password: str):
    users = _load_users()
    u = users.get(username)
    if not u:
        return None
    if _hash_password(password, u["salt"]) == u["pwd"]:
        return {
            "username": username,
            "role": u.get("role", "user"),
            "first_name": u.get("first_name", ""),
            "last_name": u.get("last_name", ""),
        }
    return None

def register_user(username: str, password: str, role: str = "user", first_name: str = "", last_name: str = ""):
    if role not in ("user", "superadmin"):
        raise ValueError("Invalid role")
    users = _load_users()
    if username in users:
        raise ValueError("Username already exists")
    salt = secrets.token_hex(16)
    users[username] = {
        "salt": salt,
        "pwd": _hash_password(password, salt),
        "role": role,
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "created_at": int(time.time()),
    }
    _save_users(users)
    return True

# ----------------- token helpers (URL query param) -----------------
TOKEN_TTL_SECONDS = 7 * 24 * 3600  # 7 days persistence

def issue_token(username: str) -> str:
    u = _get_user_record(username) or {}
    tokens = _load_tokens()
    token = secrets.token_urlsafe(24)
    now = int(time.time())
    tokens[token] = {
        "username": username,
        "role": u.get("role", "user"),
        "first_name": u.get("first_name", ""),
        "last_name": u.get("last_name", ""),
        "created_at": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }
    _save_tokens(tokens)
    return token

def validate_token(token: str | None):
    if not token:
        return None
    tokens = _load_tokens()
    entry = tokens.get(token)
    if not entry:
        return None
    if int(time.time()) > int(entry.get("exp", 0)):
        tokens.pop(token, None)
        _save_tokens(tokens)
        return None
    return {
        "username": entry.get("username"),
        "role": entry.get("role", "user"),
        "first_name": entry.get("first_name", ""),
        "last_name": entry.get("last_name", ""),
        "token": token,
    }

def revoke_token(token: str | None):
    if not token:
        return
    tokens = _load_tokens()
    if token in tokens:
        tokens.pop(token, None)
        _save_tokens(tokens)

# ----------------- Streamlit UI helpers -----------------
def _set_query_token(token: str | None):
    qp = st.query_params
    if token:
        qp["auth"] = token
    else:
        if "auth" in qp:
            del qp["auth"]

def login_form():
    st.subheader("Login")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user = authenticate(username, password)
            if user:
                st.session_state["user"] = user
                token = issue_token(user["username"])
                _set_query_token(token)
                st.session_state["auth_view"] = None
                st.session_state["active_page"] = "Valve Data"
                st.success(f"Welcome, {user['first_name'] or user['username']}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

def register_form():
    st.subheader("Register user (superadmin only)")
    if st.session_state.get("user", {}).get("role") != "superadmin":
        st.info("Only superadmin can register new users.")
        return

    with st.form("register_form", clear_on_submit=True):
        first_name = st.text_input("First name")
        last_name  = st.text_input("Last name")
        username   = st.text_input("Username")
        password   = st.text_input("Password", type="password")
        role       = st.selectbox("Role", ["user", "superadmin"], index=0)
        submitted  = st.form_submit_button("Create user")
        if submitted:
            if not username or not password:
                st.error("Username and password are required.")
            else:
                try:
                    register_user(username, password, role, first_name, last_name)
                    st.success(f"User '{username}' created with role '{role}'.")
                except ValueError as e:
                    st.error(str(e))

def logout_now():
    """Logout helper for app.py (remove session user and revoke URL token)."""
    token = st.query_params.get("auth")
    if isinstance(token, list):
        token = token[0] if token else None
    if token:
        revoke_token(token)
    try:
        _set_query_token(None)
    except Exception:
        pass
    st.session_state.pop("user", None)
    st.session_state["auth_view"] = "login"
    st.rerun()
