import requests
import streamlit as st
from config.firebase_config import FIREBASE_API_KEY

_BASE = "https://identitytoolkit.googleapis.com/v1/accounts"

_ERROR_MAP = {
    "EMAIL_NOT_FOUND"           : "No account found with this email.",
    "INVALID_PASSWORD"          : "Incorrect password.",
    "INVALID_LOGIN_CREDENTIALS" : "Incorrect email or password.",
    "INVALID_EMAIL"             : "Invalid email address.",
    "USER_DISABLED"             : "This account has been disabled.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Please try again later.",
    "EMAIL_EXISTS"              : "Email already registered — sign in instead.",
    "WEAK_PASSWORD"             : "Password must be at least 6 characters.",
    "MISSING_PASSWORD"          : "Password is required.",
    "MISSING_EMAIL"             : "Email is required.",
}

AUTH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Oswald', 'Roboto', sans-serif !important; color: #333333 !important; }
.stApp { background: linear-gradient(145deg,#E8F0FA 0%,#F5F5F5 55%,#FFFBF0 100%) !important; }
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

div[data-baseweb="input"] input, .stTextInput input {
    background: #FFFFFF !important;
    border: 1px solid #C0CDD8 !important;
    border-radius: 4px !important;
    color: #333333 !important;
    font-family: 'Roboto Mono', monospace !important;
    font-size: 0.88rem !important;
}
div[data-baseweb="input"] input:focus { border-color: #0058A3 !important; box-shadow: 0 0 0 2px rgba(0,88,163,0.15) !important; }

.stFormSubmitButton > button {
    background: #FFDA1A !important;
    color: #333333 !important;
    border: none !important;
    border-radius: 4px !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    font-family: 'Roboto Mono', monospace !important;
    letter-spacing: 1px !important;
    width: 100% !important;
    min-height: 40px !important;
    text-transform: uppercase !important;
    transition: background 0.15s !important;
}
.stFormSubmitButton > button:hover { background: #E5C500 !important; }

div[data-testid="stTabs"] button {
    font-family: 'Roboto Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 1px !important;
    color: #99A0AA !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] { color: #0058A3 !important; }

.stSuccess { background: #E8FEEE !important; color: #1A7A2A !important; border: 1px solid #AAFFBB !important; border-radius: 4px !important; }
.stError   { background: #FEE8E8 !important; color: #CC2200 !important; border: 1px solid #FFBBAA !important; border-radius: 4px !important; }

.auth-card {
    background: #FFFFFF;
    border: 1px solid #C0CDD8;
    border-radius: 12px;
    padding: 32px 28px 28px 28px;
    margin: 32px auto 0 auto;
    box-shadow: 0 4px 24px rgba(0,88,163,0.08);
}
.auth-logo-row {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 22px;
    padding-bottom: 18px;
    border-bottom: 1px solid #D8E3EC;
}
.auth-logo {
    width: 56px; height: 56px;
    background: #0058A3;
    color: #ffffff;
    font-family: 'Oswald', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
    letter-spacing: 1px;
}
.auth-app-name {
    font-family: 'Oswald', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #333333;
    letter-spacing: 1px;
    text-align: center;
}
.auth-app-sub {
    font-family: 'Roboto Mono', monospace;
    font-size: 0.62rem;
    color: #99A0AA;
    letter-spacing: 0.5px;
    margin-top: 3px;
    text-align: center;
}
.auth-divider {
    height: 1px;
    background: #D8E3EC;
    margin: 14px 0;
}
</style>
"""


def _post(endpoint: str, payload: dict) -> dict:
    try:
        r = requests.post(
            f"{_BASE}{endpoint}?key={FIREBASE_API_KEY}",
            json=payload,
            timeout=10,
        )
        return r.json()
    except requests.exceptions.RequestException as e:
        return {"error": {"message": f"Network error: {e}"}}


def _friendly(raw: str) -> str:
    for key, msg in _ERROR_MAP.items():
        if key in raw:
            return msg
    return raw


def render_auth() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)

        # ── Branding ─────────────────────────────────────────────
        st.markdown("""
        <div class="auth-logo-row">
            <div class="auth-logo">Q</div>
            <div class="auth-app-name">QUERY ANALYZER</div>
            <div class="auth-app-sub">BERT · GROQ ENGINE · FIREBASE AUTH</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Tabs ─────────────────────────────────────────────────
        tab_in, tab_up, tab_pw = st.tabs(["▸ SIGN IN", "▸ SIGN UP", "▸ RESET PASSWORD"])

        # ── Sign In ───────────────────────────────────────────────
        with tab_in:
            with st.form("_signin"):
                email    = st.text_input("EMAIL",    placeholder="you@example.com",  key="si_email")
                password = st.text_input("PASSWORD", placeholder="••••••••",          key="si_pw", type="password")
                ok       = st.form_submit_button("SIGN IN", use_container_width=True)

            if ok:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Signing in…"):
                        res = _post(":signInWithPassword", {
                            "email": email, "password": password, "returnSecureToken": True,
                        })
                    if "idToken" in res:
                        st.session_state.user = {
                            "email"  : res["email"],
                            "idToken": res["idToken"],
                            "uid"    : res["localId"],
                        }
                        st.success("Signed in successfully!")
                        st.rerun()
                    else:
                        raw = res.get("error", {}).get("message", "Sign-in failed.")
                        st.error(_friendly(raw))

        # ── Sign Up ───────────────────────────────────────────────
        with tab_up:
            with st.form("_signup"):
                email   = st.text_input("EMAIL",            placeholder="you@example.com", key="su_email")
                pw1     = st.text_input("PASSWORD",         placeholder="min 6 chars",     key="su_pw1",  type="password")
                pw2     = st.text_input("CONFIRM PASSWORD", placeholder="••••••••",        key="su_pw2",  type="password")
                ok      = st.form_submit_button("CREATE ACCOUNT", use_container_width=True)

            if ok:
                if not email or not pw1 or not pw2:
                    st.error("Please fill in all fields.")
                elif pw1 != pw2:
                    st.error("Passwords do not match.")
                else:
                    with st.spinner("Creating account…"):
                        res = _post(":signUp", {
                            "email": email, "password": pw1, "returnSecureToken": True,
                        })
                    if "idToken" in res:
                        st.session_state.user = {
                            "email"  : res["email"],
                            "idToken": res["idToken"],
                            "uid"    : res["localId"],
                        }
                        st.success("Account created! Welcome.")
                        st.rerun()
                    else:
                        raw = res.get("error", {}).get("message", "Sign-up failed.")
                        st.error(_friendly(raw))

        # ── Reset Password ────────────────────────────────────────
        with tab_pw:
            with st.form("_reset"):
                email = st.text_input("EMAIL", placeholder="you@example.com", key="rp_email")
                ok    = st.form_submit_button("SEND RESET EMAIL", use_container_width=True)

            if ok:
                if not email:
                    st.error("Please enter your email address.")
                else:
                    with st.spinner("Sending…"):
                        res = _post(":sendOobCode", {
                            "requestType": "PASSWORD_RESET", "email": email,
                        })
                    if "email" in res:
                        st.success(f"Reset email sent to {email}. Check your inbox.")
                    else:
                        raw = res.get("error", {}).get("message", "Failed to send reset email.")
                        st.error(_friendly(raw))

        st.markdown("</div>", unsafe_allow_html=True)
