# ───────────────────────────────────────────────────────────────
#cdm
# projenv\Scripts\activate
# uv run streamlit run app.py

# ───────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd

# ── Load user credentials and profiles ────────────────────────
CREDENTIALS = dict(st.secrets["auth"])
PROFILES = st.secrets.get("profile", {})

# ── Login form ────────────────────────────────────────────────
def login():
    st.title("🔐 Login Required")

    user = st.text_input("Username", key="username_input")
    password = st.text_input("Password", type="password", key="password_input")

    if st.button("Login", key="login_button"):
        if user in CREDENTIALS and password == CREDENTIALS[user]:
            st.session_state["authenticated"] = True
            st.session_state["username"] = user
            st.session_state["first_name"] = PROFILES.get(user, {}).get("first_name", user)
        else:
            st.error("❌ Invalid username or password")

# ── Auth state setup ──────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# ── Login gate ────────────────────────────────────────────────
if not st.session_state["authenticated"]:
    login()
    st.stop()

# ── App begins after login ────────────────────────────────────

# ---------------Sidebar
from utils import apply_style_and_logo

st.sidebar.success(f"Welcome {st.session_state['first_name']}!")
st.sidebar.button("Logout", on_click=lambda: st.session_state.update(authenticated=False))


# Spacer to push the link to the bottom (optional tweak for better placement)
st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# Company website link
st.sidebar.markdown(
    '<p style="text-align:center;">'
    '<a href="https://www.wavetransition.com" target="_blank">🌐 Visit WaveTransition</a>'
    '</p>',
    unsafe_allow_html=True
)
# ---------Main content
st.set_page_config(page_title="Comaonies Dashboard", layout="wide")
st.title("WAVETRANSITION COMPANIES SCOUTING ")
st.markdown(
    """
    <h1 style='text-align: center; color: #005680;'>
        WAVETRANSITION COMPANIES SEARCH APPLICATION
    </h1>
    """,
    unsafe_allow_html=True
)

# --- Centered cover image ---
from PIL import Image
cover_img = Image.open("cover.png")
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.image(cover_img, use_container_width=False, width=800)  # updated
#st.image(cover_img, use_container_width=True)  # auto fit


st.markdown("</div>", unsafe_allow_html=True)

# --- Welcome text ---
st.markdown(
    """
    <div style='text-align: left; font-size: 20px;'>
        <p>Welcome to <b>COMPANY SEARCH APPLICATION</b></p>
        <p>Explore and analyze companies from our <b>proprietary curated database</b>, 
        filter by <b>country, business domain</b>, and <b>energy domain</b>, 
        and enrich profiles with external web intelligence.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Horizontal line ---
st.markdown("---")

# --- Key Features ---
st.markdown(
    """
    ### 📌 **Key Features**
    - Search and explore companies from a **proprietary curated database**
    - Filter by **country, business domain, and energy domain**
    - Access **company websites** and external market information in one click
    - Integrated **web intelligence** to enrich company profiles

    ### 🌍 **Coverage**
    The data in this app comes from a **privately maintained company database**, 
    covering organizations across multiple sectors and geographies.

    ### ⚠️ **Note**
    This app focuses on **company-level insights** combining internal data with 
    external sources. Detailed sector reports and market forecasts are available in other WT's applications.
    """
)
