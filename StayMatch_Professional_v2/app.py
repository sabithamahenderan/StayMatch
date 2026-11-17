"""
StayMatch — Smart PG Finder and Recommendation System for Tamil Nadu.
Run locally: streamlit run app.py
"""
import re
import json
import html
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from constants import (
    TAMIL_NADU_DISTRICTS, TN_REGIONS, AMENITIES,
    SHARING_OPTIONS, FOOD_OPTIONS, GENDER_OPTIONS, AC_OPTIONS,
    get_listing_image
)
from database import (
    init_db, register_user, authenticate_user,
    get_all_listings, get_listing, add_listing, update_listing, delete_listing,
    toggle_saved, get_saved_ids, get_saved_listings,
    record_search, get_search_history, delete_search_history, clear_all_search_history,
    record_view, get_view_history, dashboard_stats, get_district_summary
)
from recommender import (
    recommend_listings, score_listing, get_alternative_recommendations, parse_amenities
)

# ---------------------------------------------------------
# Page Configuration & Global Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="StayMatch | Smart PG Finder & Recommendation System",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema and initial data
init_db()

# Custom SaaS-Style Theme Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --primary: #1e40af;
    --primary-light: #3b82f6;
    --primary-soft: #eff6ff;
    --dark: #0f172a;
    --slate: #475569;
    --light-slate: #94a3b8;
    --border: #e2e8f0;
    --bg-light: #f8fafc;
    --card-bg: #ffffff;
    --success: #059669;
    --success-bg: #ecfdf5;
    --warning: #d97706;
    --danger: #dc2626;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
    color: var(--dark);
}

.stApp {
    background-color: #f8fafc;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #091326 0%, #0f2347 50%, #173b75 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

[data-testid="stSidebar"] * {
    color: #f1f5f9 !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.12) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #94a3b8 !important;
}

/* Typography */
h1, h2, h3, h4 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.025em;
    font-weight: 700 !important;
    color: #0f172a;
}

/* Main Container spacing */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3.5rem;
    max-width: 1400px;
}

/* Hero Section */
.hero-banner {
    background: linear-gradient(125deg, #091a3c 0%, #1e3a8a 55%, #2563eb 100%);
    border-radius: 20px;
    padding: 38px 42px;
    color: #ffffff;
    margin-bottom: 24px;
    box-shadow: 0 12px 32px -4px rgba(30, 58, 138, 0.25);
    position: relative;
    overflow: hidden;
}

.hero-banner::after {
    content: '';
    position: absolute;
    top: -50px;
    right: -50px;
    width: 250px;
    height: 250px;
    background: radial-gradient(circle, rgba(96, 165, 250, 0.22) 0%, rgba(96, 165, 250, 0) 70%);
    border-radius: 50%;
    pointer-events: none;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.14);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #93c5fd;
    margin-bottom: 12px;
}

.hero-title {
    font-size: 2.35rem;
    font-weight: 800;
    line-height: 1.2;
    margin: 0 0 10px 0;
    color: #ffffff !important;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: #dbeafe;
    max-width: 720px;
    line-height: 1.55;
    margin: 0 0 20px 0;
}

/* Metric KPI Cards */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 18px 22px;
    box-shadow: 0 4px 14px -2px rgba(15, 23, 42, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px -3px rgba(37, 99, 235, 0.12);
    border-color: #cbd5e1;
}

[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

[data-testid="stMetricValue"] {
    color: #1e3a8a !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.75rem !important;
}

/* SaaS Listing Card */
.pg-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    overflow: hidden;
    margin-bottom: 18px;
    box-shadow: 0 4px 18px -2px rgba(15, 23, 42, 0.04);
    transition: all 0.22s ease-in-out;
}

.pg-card:hover {
    border-color: #93c5fd;
    box-shadow: 0 12px 28px -4px rgba(37, 99, 235, 0.12);
    transform: translateY(-3px);
}

.pg-card-img {
    width: 100%;
    height: 190px;
    object-fit: cover;
    border-radius: 14px;
    margin-bottom: 8px;
}

/* Badges & Pills */
.pill-amenity {
    display: inline-block;
    padding: 4px 10px;
    background: #eff6ff;
    color: #1e40af;
    border: 1px solid #dbeafe;
    border-radius: 8px;
    font-size: 0.74rem;
    font-weight: 600;
    margin: 2px 4px 2px 0;
}

.pill-badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 6px;
}

.badge-available {
    background: #ecfdf5;
    color: #059669;
    border: 1px solid #a7f3d0;
}

.badge-full {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
}

.badge-gender {
    background: #f1f5f9;
    color: #334155;
    border: 1px solid #e2e8f0;
}

.match-score-badge {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border: 1px solid #bfdbfe;
    color: #1e40af;
    padding: 6px 14px;
    border-radius: 10px;
    font-size: 0.84rem;
    font-weight: 700;
    margin: 8px 0;
}

.match-score-badge span {
    color: #2563eb;
    font-size: 1.05rem;
    margin-right: 6px;
}

.alt-banner {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 12px 18px;
    border-radius: 8px;
    margin: 14px 0 20px 0;
    color: #92400e;
    font-size: 0.92rem;
}

/* Button overrides */
.stButton>button, .stFormSubmitButton>button {
    border-radius: 11px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    min-height: 2.6rem;
    border: 1px solid #cbd5e1 !important;
    transition: all 0.18s ease-in-out !important;
}

.stButton>button:hover, .stFormSubmitButton>button:hover {
    border-color: #2563eb !important;
    color: #1e40af !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15) !important;
}

.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    border-color: #1d4ed8 !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28) !important;
}

.stButton>button[kind="primary"]:hover, .stFormSubmitButton>button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%) !important;
    box-shadow: 0 6px 18px rgba(30, 58, 138, 0.35) !important;
}

/* Auth card */
.auth-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 32px 36px;
    box-shadow: 0 10px 30px -4px rgba(15, 23, 42, 0.08);
    margin-top: 2rem;
}

/* District Card */
.district-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 14px;
    transition: all 0.2s ease;
}

.district-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 6px 18px -2px rgba(37, 99, 235, 0.1);
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Authentication Screen
# ---------------------------------------------------------
def render_auth_screen():
    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px; margin-top: 1rem;">
            <div style="font-size: 2.8rem; margin-bottom: 6px;">🏡</div>
            <h1 style="font-size: 2.1rem; margin: 0; color: #0f172a;">StayMatch</h1>
            <p style="color: #64748b; font-size: 0.98rem; margin-top: 4px;">Smart PG Finder & Recommendation System · Tamil Nadu</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Account"])
            with tab_login:
                with st.form("login_form"):
                    st.markdown("#### Welcome Back")
                    st.caption("Sign in to discover accommodations and save your favorites.")
                    login_email = st.text_input("Email address", placeholder="you@example.com")
                    login_password = st.text_input("Password", type="password", placeholder="Enter your account password")
                    submit_login = st.form_submit_button("Sign in to StayMatch", type="primary", use_container_width=True)

                if submit_login:
                    if not login_email or not login_password:
                        st.error("Please enter both your email address and password.")
                    else:
                        authenticated_user = authenticate_user(login_email, login_password)
                        if authenticated_user:
                            st.session_state.user = authenticated_user
                            st.session_state.saved_ids = get_saved_ids(authenticated_user["id"])
                            st.success(f"Welcome back, {authenticated_user['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid email or password. Please check your credentials.")

            with tab_register:
                with st.form("register_form"):
                    st.markdown("#### Create New Account")
                    st.caption("Takes less than a minute. Save your searches and favorite PGs.")
                    reg_name = st.text_input("Full name", placeholder="Your name")
                    reg_email = st.text_input("Email address", placeholder="you@example.com")
                    reg_pass1 = st.text_input("Create password", type="password", help="At least 8 characters with a letter and a number.")
                    reg_pass2 = st.text_input("Confirm password", type="password")
                    submit_register = st.form_submit_button("Create My Account", type="primary", use_container_width=True)

                if submit_register:
                    if not reg_name.strip() or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", reg_email.strip()):
                        st.error("Please provide your full name and a valid email address.")
                    elif len(reg_pass1) < 8 or not re.search(r"[A-Za-z]", reg_pass1) or not re.search(r"\d", reg_pass1):
                        st.error("Password must be at least 8 characters long and contain both letters and numbers.")
                    elif reg_pass1 != reg_pass2:
                        st.error("Passwords do not match. Please re-enter them carefully.")
                    else:
                        try:
                            new_user = register_user(reg_name, reg_email, reg_pass1)
                            st.session_state.user = dict(new_user)
                            st.session_state.saved_ids = set()
                            st.success("Account created successfully! Welcome to StayMatch.")
                            st.rerun()
                        except Exception:
                            st.error("An account with this email address already exists. Please sign in instead.")

        st.caption("🔒 All user passwords are encrypted using salted PBKDF2-HMAC-SHA256 hashes.")

# Check authentication
if "user" not in st.session_state:
    render_auth_screen()
    st.stop()

# Current authenticated user
current_user = st.session_state.user
uid = int(current_user["id"])

# Initialize session cache for saved listing IDs and comparison list
if "saved_ids" not in st.session_state:
    st.session_state.saved_ids = get_saved_ids(uid)
if "compare_ids" not in st.session_state:
    st.session_state.compare_ids = []
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Load latest dataset
df_listings = get_all_listings()
all_records = df_listings.to_dict("records") if not df_listings.empty else []

def fmt_money(val):
    try:
        return f"₹{int(val):,}"
    except (ValueError, TypeError):
        return "₹0"

# ---------------------------------------------------------
# Reusable UI Component: Modern PG Listing Card
# ---------------------------------------------------------
def render_pg_card(row, score=None, matched_reasons=None, alt_reason=None, show_actions=True, context_key=""):
    lid = int(row["id"])
    is_saved = lid in st.session_state.saved_ids
    in_compare = lid in st.session_state.compare_ids
    img_url = get_listing_image(lid, row.get("gender_policy", "Co-living"), row.get("image_url", ""))
    amenity_list = [x.strip() for x in str(row.get("amenities", "")).split(",") if x.strip()]

    with st.container(border=True):
        col_img, col_body, col_side = st.columns([1.1, 2.3, 1.0])

        with col_img:
            st.image(img_url, use_container_width=True)
            # Status badges
            vac_badge = '<span class="pill-badge badge-available">🟢 Available</span>' if int(row.get("vacancy", 0)) else '<span class="pill-badge badge-full">🔴 Occupied</span>'
            gender_badge = f'<span class="pill-badge badge-gender">{html.escape(str(row.get("gender_policy", "Co-living")))}</span>'
            st.markdown(f"<div style='margin-top: -4px;'>{vac_badge}{gender_badge}</div>", unsafe_allow_html=True)

        with col_body:
            st.markdown(f"<h3 style='margin: 0 0 4px 0; font-size: 1.22rem;'>{html.escape(row['name'])}</h3>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='color: #475569; font-size: 0.88rem; margin-bottom: 6px;'>"
                f"📍 <strong>{html.escape(row['locality'])}, {html.escape(row['district'])}</strong> · "
                f"<span style='color: #1e40af; font-weight: 600;'>{html.escape(row['sharing'])}</span> · "
                f"<span>Food: {html.escape(str(row.get('food', 'Optional')))}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

            # Match Score / Alternative explanation
            if score is not None:
                reasons_text = ", ".join(matched_reasons) if matched_reasons else "Core criteria matched"
                st.markdown(
                    f"<div class='match-score-badge'>"
                    f"<span>✨ {score}% Match</span> {html.escape(reasons_text)}"
                    f"</div>",
                    unsafe_allow_html=True
                )
            elif alt_reason:
                st.markdown(
                    f"<div style='background: #fffbeb; border: 1px solid #fef3c7; color: #b45309; padding: 4px 10px; border-radius: 6px; font-size: 0.82rem; font-weight: 600; margin: 4px 0;'>"
                    f"💡 {html.escape(alt_reason)}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # Description snippet
            desc = (row.get("description") or "Comfortable PG accommodation with verified facilities.")[:160]
            st.caption(f"{desc}...")

            # Amenity pills
            pills_html = "".join([f'<span class="pill-amenity">{html.escape(a)}</span>' for a in amenity_list[:6]])
            if len(amenity_list) > 6:
                pills_html += f'<span class="pill-amenity" style="background:#f1f5f9; color:#64748b;">+{len(amenity_list)-6} more</span>'
            st.markdown(f"<div>{pills_html}</div>", unsafe_allow_html=True)

            # Transparency notice
            is_synthetic = "Synthetic" in str(row.get("source_type", "")) or str(row.get("source_type", "")) == "Synthetic demo data"
            source_label = "Demo Listing (Sample Data)" if is_synthetic else "Community Submitted"
            st.caption(f"ℹ️ {source_label} · Distance: {float(row.get('distance_km', 0) or 0):g} km")

        with col_side:
            st.markdown(f"<div style='text-align: right;'><span style='font-size: 1.55rem; font-weight: 800; color: #1e3a8a;'>{fmt_money(row['rent'])}</span><span style='color: #64748b; font-size: 0.85rem;'> / month</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: right; color: #64748b; font-size: 0.8rem; margin-bottom: 10px;'>Deposit: {fmt_money(row.get('deposit', 0))}</div>", unsafe_allow_html=True)

            if show_actions:
                # View Details Button
                if st.button("View Details", key=f"btn_det_{context_key}_{lid}", type="primary", use_container_width=True):
                    st.session_state.selected_listing = lid
                    st.session_state.previous_page = st.session_state.page
                    st.session_state.page = "PG details"
                    st.rerun()

                # Action row: Save & Compare
                b1, b2 = st.columns(2)
                with b1:
                    save_label = "❤️ Saved" if is_saved else "🤍 Save"
                    if st.button(save_label, key=f"btn_sav_{context_key}_{lid}", use_container_width=True):
                        new_state = toggle_saved(uid, lid)
                        if new_state:
                            st.session_state.saved_ids.add(lid)
                        else:
                            st.session_state.saved_ids.discard(lid)
                        st.rerun()

                with b2:
                    cmp_label = "✓ Compare" if in_compare else "⚖️ Compare"
                    if st.button(cmp_label, key=f"btn_cmp_{context_key}_{lid}", use_container_width=True):
                        if in_compare:
                            st.session_state.compare_ids.remove(lid)
                        else:
                            if len(st.session_state.compare_ids) >= 4:
                                st.warning("You can compare up to 4 PGs at a time.")
                            else:
                                st.session_state.compare_ids.append(lid)
                        st.rerun()

# ---------------------------------------------------------
# Sidebar Navigation & Branding
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; padding: 6px 0 12px 0;">
        <span style="font-size: 2.2rem;">🏡</span>
        <div>
            <h2 style="margin: 0; font-size: 1.45rem; color: #ffffff !important; letter-spacing: -0.02em;">StayMatch</h2>
            <div style="font-size: 0.72rem; color: #93c5fd !important; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">Tamil Nadu PG Portal</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**👤 {html.escape(current_user['name'])}**")
    st.caption(f"{html.escape(current_user['email'])}")
    st.divider()

    nav_options = [
        "🏠 Home Dashboard",
        "🔍 Smart PG Finder",
        "🗺️ Explore Tamil Nadu",
        "⚖️ Compare PGs",
        "❤️ Saved & History",
        "📊 Analytics Dashboard",
        "⚙️ Listing Management"
    ]

    # Map current state to radio
    nav_keys = {
        "Home": "🏠 Home Dashboard",
        "Smart PG Finder": "🔍 Smart PG Finder",
        "Explore Tamil Nadu": "🗺️ Explore Tamil Nadu",
        "Compare PGs": "⚖️ Compare PGs",
        "Saved & History": "❤️ Saved & History",
        "Analytics Dashboard": "📊 Analytics Dashboard",
        "Listing Management": "⚙️ Listing Management",
        "PG details": None
    }

    if st.session_state.page == "PG details":
        st.info("Currently viewing listing details")
        if st.button("← Return to Listings", use_container_width=True, type="primary"):
            st.session_state.page = st.session_state.get("previous_page", "Home")
            st.rerun()
    else:
        current_nav = nav_keys.get(st.session_state.page, "🏠 Home Dashboard")
        selected_nav = st.radio(
            "NAVIGATION",
            nav_options,
            index=nav_options.index(current_nav) if current_nav in nav_options else 0,
            label_visibility="collapsed"
        )
        # Update page if changed via sidebar
        raw_page_name = selected_nav.split(" ", 1)[1]
        if raw_page_name == "Home Dashboard":
            raw_page_name = "Home"
        if st.session_state.page != raw_page_name and st.session_state.page != "PG details":
            st.session_state.page = raw_page_name
            st.rerun()

    st.divider()

    # Sidebar Quick Stats & Badges
    stats_quick = dashboard_stats()
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.06); padding: 12px; border-radius: 12px; font-size: 0.82rem; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #94a3b8;">Total Listings:</span>
            <strong style="color: #ffffff;">{stats_quick['total']}</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #94a3b8;">Available Now:</span>
            <strong style="color: #34d399;">{stats_quick['available']}</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #94a3b8;">Districts:</span>
            <strong style="color: #60a5fa;">{len(TAMIL_NADU_DISTRICTS)} / 38</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #94a3b8;">Compare Queue:</span>
            <strong style="color: #fbbf24;">{len(st.session_state.compare_ids)} selected</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ---------------------------------------------------------
# View: PG Details Screen
# ---------------------------------------------------------
def render_details_page():
    lid = st.session_state.get("selected_listing")
    item = get_listing(lid) if lid else None

    if not item:
        st.error("Listing not found or could not be loaded.")
        if st.button("← Return"):
            st.session_state.page = st.session_state.get("previous_page", "Home")
            st.rerun()
        return

    # Record user view history
    record_view(uid, lid)

    # Top Breadcrumb & Back button
    b_col1, b_col2 = st.columns([1, 4])
    with b_col1:
        if st.button("← Back to listings", key="back_from_details", use_container_width=True):
            st.session_state.page = st.session_state.get("previous_page", "Home")
            st.rerun()
    with b_col2:
        st.markdown(f"<span style='color: #64748b;'>Home / {html.escape(item['district'])} / {html.escape(item['locality'])} / <strong>{html.escape(item['name'])}</strong></span>", unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Header Row
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown(f"<h1 style='margin: 0 0 6px 0; font-size: 2.2rem;'>{html.escape(item['name'])}</h1>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-size: 1.05rem; color: #475569;'>"
            f"📍 {html.escape(item['locality'])}, {html.escape(item['city'])}, <strong>{html.escape(item['district'])} District</strong>, Tamil Nadu · "
            f"<span style='color: #1e40af; font-weight: 600;'>{html.escape(item['gender_policy'])}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
    with h_col2:
        st.markdown(f"<div style='text-align: right;'><span style='font-size: 2rem; font-weight: 800; color: #1e3a8a;'>{fmt_money(item['rent'])}</span><span style='color: #64748b;'>/month</span></div>", unsafe_allow_html=True)
        vac_text = "🟢 Available Now" if int(item.get("vacancy", 0)) else "🔴 Currently Occupied"
        st.markdown(f"<div style='text-align: right; font-weight: 700;'>{vac_text}</div>", unsafe_allow_html=True)

    st.divider()

    # Image and Quick Highlights
    img_url = get_listing_image(item["id"], item.get("gender_policy", "Co-living"), item.get("image_url", ""))
    img_col, info_col = st.columns([1.5, 1])

    with img_col:
        st.image(img_url, use_container_width=True)
        # Action buttons
        a1, a2 = st.columns(2)
        with a1:
            is_saved = item["id"] in st.session_state.saved_ids
            save_txt = "❤️ Saved to Favorites" if is_saved else "🤍 Save to Favorites"
            if st.button(save_txt, key="det_fav_btn", use_container_width=True):
                new_state = toggle_saved(uid, item["id"])
                if new_state:
                    st.session_state.saved_ids.add(item["id"])
                else:
                    st.session_state.saved_ids.discard(item["id"])
                st.rerun()
        with a2:
            in_cmp = item["id"] in st.session_state.compare_ids
            cmp_txt = "✓ In Compare Queue" if in_cmp else "⚖️ Add to Compare"
            if st.button(cmp_txt, key="det_cmp_btn", use_container_width=True):
                if in_cmp:
                    st.session_state.compare_ids.remove(item["id"])
                else:
                    st.session_state.compare_ids.append(item["id"])
                st.rerun()

    with info_col:
        with st.container(border=True):
            st.markdown("### 🏷️ Key Highlights")
            st.markdown(f"**Monthly Rent:** {fmt_money(item['rent'])}")
            st.markdown(f"**Security Deposit:** {fmt_money(item.get('deposit', 0))}")
            st.markdown(f"**Sharing Type:** {item['sharing']}")
            st.markdown(f"**Accommodation For:** {item['gender_policy']}")
            st.markdown(f"**Food Availability:** {item.get('food', 'Not specified')}")
            st.markdown(f"**Distance to City Hub/College:** {float(item.get('distance_km', 0) or 0):g} km")
            st.markdown(f"**Contact Number:** `{item.get('contact') or 'Available on visit request'}`")
            st.caption("🔒 Verify rent, rules, and room vacancy directly before making advance payments.")

    # Detailed Tabs
    st.markdown("### 📋 Accommodation Details")
    tab_overview, tab_amenities, tab_food, tab_rules, tab_contact = st.tabs([
        "🏡 Overview & Description",
        "✨ Facilities & Amenities",
        "🍽️ Food & Meals",
        "📜 House Rules",
        "📞 Contact & Inquiries"
    ])

    with tab_overview:
        st.write(item.get("description") or "Comfortable and safe paying guest accommodation with clean rooms and essential conveniences.")
        st.markdown(f"""
        - **District:** {item['district']}
        - **Locality:** {item['locality']}
        - **City:** {item['city']}
        - **State:** Tamil Nadu
        - **Listing Source:** {"Synthetic Demonstration Data (Project Prototype)" if "Synthetic" in str(item.get("source_type", "")) else "User/Owner Submitted"}
        """)

    with tab_amenities:
        amenities = [a.strip() for a in str(item.get("amenities", "")).split(",") if a.strip()]
        if amenities:
            cols = st.columns(3)
            for i, a in enumerate(amenities):
                cols[i % 3].markdown(f"✅ **{html.escape(a)}**")
        else:
            st.info("No specific amenities specified.")

    with tab_food:
        st.markdown(f"**Food Provision:** {item.get('food', 'Not specified')}")
        st.markdown(f"**Meal Timing & Details:** {item.get('food_meals') or 'Three meals a day (Breakfast, Lunch, Dinner) available on request.'}")

    with tab_rules:
        st.markdown("**House Rules & Timings:**")
        st.write(item.get("rules") or "Standard PG guidelines apply. Gate closes by 10:00 PM. Visitors allowed in the reception/common area only. Cleanliness and mutual respect expected.")

    with tab_contact:
        st.markdown("#### Provider Communication")
        st.markdown(f"**Contact Person / Phone:** `{item.get('contact') or 'Contact desk available upon visit'}`")
        st.info("Disclaimer: This application uses synthetic demonstration listings for Tamil Nadu academic evaluation. Always independently verify physical rooms and contact info.")

# ---------------------------------------------------------
# View 1: Home Dashboard
# ---------------------------------------------------------
if st.session_state.page == "Home":
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-badge">🌟 Tamil Nadu's Smart Student & Professional Accommodation Network</div>
        <h1 class="hero-title">Find a PG That Feels Like Home.</h1>
        <p class="hero-subtitle">
            Discover verified Paying Guest accommodations across all 38 districts of Tamil Nadu.
            Match your budget, sharing preferences, food, and lifestyle in one place.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Key Statistics Row
    stats = dashboard_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total PG Listings", stats["total"], help="Total PG properties cataloged across Tamil Nadu")
    m2.metric("Available Accommodations", stats["available"], help="Properties with immediate room vacancy")
    m3.metric("Tamil Nadu Districts", f"{stats['districts']} / 38", help="District coverage across Tamil Nadu")
    m4.metric("Average Listed Rent", fmt_money(stats["average_rent"]), help="State-wide average monthly rent for vacant accommodations")

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Quick Action Cards
    st.markdown("### ⚡ Quick Exploration")
    q1, q2, q3 = st.columns(3)

    with q1:
        with st.container(border=True):
            st.markdown("#### 🔎 Smart PG Finder")
            st.write("Filter by district, budget, sharing type, AC, food, and 10+ facilities.")
            if st.button("Launch Smart Search →", type="primary", use_container_width=True):
                st.session_state.page = "Smart PG Finder"
                st.rerun()

    with q2:
        with st.container(border=True):
            st.markdown("#### 🗺️ Explore Tamil Nadu")
            st.write("Browse PG availability across all 38 districts with regional groupings.")
            if st.button("Explore by District →", use_container_width=True):
                st.session_state.page = "Explore Tamil Nadu"
                st.rerun()

    with q3:
        with st.container(border=True):
            st.markdown("#### 📊 Market Analytics")
            st.write("View rent trends, sharing distributions, and facility availability charts.")
            if st.button("View Analytics Dashboard →", use_container_width=True):
                st.session_state.page = "Analytics Dashboard"
                st.rerun()

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Recently Added Accommodations
    st.markdown("### 🏠 Featured & Recently Added Accommodations")
    st.caption("Showing handpicked accommodations across Tamil Nadu hubs.")

    for record in all_records[:4]:
        render_pg_card(record, context_key="home")

    # Dataset Transparency Note
    st.info("ℹ️ **Academic Dataset Transparency**: Starter records are synthetic demonstration data created for project evaluation. Contact details and vacancies should be confirmed directly with providers.")

# ---------------------------------------------------------
# View 2: Smart PG Finder
# ---------------------------------------------------------
elif st.session_state.page == "Smart PG Finder":
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <h1 style="margin: 0; font-size: 2.1rem;">Smart PG Finder</h1>
        <p style="color: #64748b; font-size: 1rem; margin-top: 4px;">
            Set your exact location, budget, and lifestyle requirements. Listings are ranked using explainable preference scoring.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("smart_pg_search_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("##### 📍 Location & Budget")
            f_district = st.selectbox("District", ["All districts"] + TAMIL_NADU_DISTRICTS, index=0)

            # Localities dynamic dropdown based on selected district
            if f_district != "All districts" and not df_listings.empty:
                loc_df = df_listings[df_listings["district"] == f_district]
                loc_options = sorted([str(x) for x in loc_df["locality"].dropna().unique() if str(x).strip()])
            else:
                loc_options = []
            f_locality = st.selectbox("City / Locality", ["Any"] + loc_options)

            budget_min = st.number_input("Minimum monthly rent (₹)", min_value=0, max_value=200000, value=3000, step=500)
            budget_max = st.number_input("Maximum monthly rent (₹)", min_value=0, max_value=300000, value=12000, step=500)

        with col2:
            st.markdown("##### 👥 Room & Board")
            f_gender = st.selectbox("Accommodation For", GENDER_OPTIONS)
            f_sharing = st.selectbox("Sharing Preference", ["Any"] + SHARING_OPTIONS)
            f_food = st.selectbox("Food Preference", FOOD_OPTIONS)
            f_ac = st.selectbox("Air Conditioning", AC_OPTIONS)
            f_avail_only = st.checkbox("Available accommodations only", value=True)

        with col3:
            st.markdown("##### ✨ Amenities & Filters")
            f_amenities = st.multiselect("Essential Facilities", AMENITIES, default=["Wi-Fi"])
            f_max_distance = st.number_input("Max distance to hub/college (km, 0 = any)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            f_sort = st.selectbox("Sort Results By", ["Highest Match Score", "Rent: Low to High", "Rent: High to Low"])

        search_submitted = st.form_submit_button("🔍 Find Matching Accommodations", type="primary", use_container_width=True)

    # Process Search Submission or Retain Results
    if search_submitted or "last_search_results" in st.session_state:
        if search_submitted:
            if budget_min > budget_max:
                st.error("Minimum monthly rent cannot exceed maximum rent.")
                st.stop()

            active_prefs = {
                "district": f_district,
                "locality": f_locality,
                "min_budget": budget_min,
                "max_budget": budget_max,
                "gender_policy": f_gender,
                "sharing": f_sharing,
                "food": f_food,
                "ac_type": f_ac,
                "amenities": f_amenities,
                "available_only": f_avail_only
            }

            # Run recommendation engine
            with st.spinner("Finding best accommodations..."):
                ranked_results = recommend_listings(all_records, active_prefs)

                # Distance filtering if set
                if f_max_distance > 0:
                    ranked_results = [x for x in ranked_results if float(x[0].get("distance_km", 0) or 0) <= f_max_distance]

                # Sorting option
                if f_sort == "Rent: Low to High":
                    ranked_results.sort(key=lambda x: int(x[0].get("rent", 0)))
                elif f_sort == "Rent: High to Low":
                    ranked_results.sort(key=lambda x: int(x[0].get("rent", 0)), reverse=True)

                # Record in search history
                record_search(uid, active_prefs, len(ranked_results))

                # Cache in session state
                st.session_state.last_search_results = ranked_results
                st.session_state.last_search_prefs = active_prefs

        results = st.session_state.get("last_search_results", [])
        prefs_used = st.session_state.get("last_search_prefs", {})

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        if results:
            st.markdown(f"### 🎯 Found {len(results)} Exact Accommodation Match(es)")
            st.caption("Each match percentage is computed strictly from your active preferences (sharing, food, AC, amenities, locality).")

            for item, score, matched in results:
                render_pg_card(item, score=score, matched_reasons=matched, context_key="finder")
        else:
            st.warning("No exact accommodations matched all your selected filters.")

            # Intelligent Alternative Recommendations
            st.markdown("""
            <div class="alt-banner">
                <strong>💡 Alternative Recommendations:</strong>
                We widened the search window to show you the closest available accommodations.
            </div>
            """, unsafe_allow_html=True)

            alternatives = get_alternative_recommendations(all_records, prefs_used, top_k=4)
            if alternatives:
                for item, score, matched, alt_reason in alternatives:
                    render_pg_card(item, score=None, matched_reasons=matched, alt_reason=alt_reason, context_key="alt_finder")
            else:
                st.info("Try broadening your budget range or selecting 'All districts'.")

# ---------------------------------------------------------
# View 3: Explore Tamil Nadu (All 38 Districts)
# ---------------------------------------------------------
elif st.session_state.page == "Explore Tamil Nadu":
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <h1 style="margin: 0; font-size: 2.1rem;">Explore Tamil Nadu</h1>
        <p style="color: #64748b; font-size: 1rem; margin-top: 4px;">
            Comprehensive coverage across all 38 districts of Tamil Nadu. Browse listings, average rents, and available rooms.
        </p>
    </div>
    """, unsafe_allow_html=True)

    district_summary = get_district_summary()

    # Search & Region filter
    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        search_district = st.text_input("🔍 Search district by name", placeholder="e.g. Chennai, Coimbatore, Madurai...")
    with f_col2:
        region_filter = st.selectbox("Region Filter", ["All Regions"] + list(TN_REGIONS.keys()))

    # Selected district drill-down in session state
    if "selected_explore_district" not in st.session_state:
        st.session_state.selected_explore_district = None

    if st.session_state.selected_explore_district:
        sel_dist = st.session_state.selected_explore_district
        if st.button("← Back to All Districts", key="back_to_districts"):
            st.session_state.selected_explore_district = None
            st.rerun()

        st.markdown(f"## 📍 PG Accommodations in {sel_dist}")
        dist_records = [r for r in all_records if r.get("district") == sel_dist]

        if dist_records:
            st.caption(f"Showing {len(dist_records)} accommodation(s) listed in {sel_dist} district.")
            for r in dist_records:
                render_pg_card(r, context_key=f"dist_{sel_dist}")
        else:
            st.info(f"No listings found currently for {sel_dist}.")

    else:
        # Display District Cards Grid
        districts_to_show = TAMIL_NADU_DISTRICTS
        if region_filter != "All Regions":
            districts_to_show = [d for d in districts_to_show if d in TN_REGIONS.get(region_filter, [])]
        if search_district.strip():
            districts_to_show = [d for d in districts_to_show if search_district.strip().lower() in d.lower()]

        # Quick stats row
        s1, s2, s3 = st.columns(3)
        s1.metric("Districts Displayed", len(districts_to_show))
        s2.metric("Total Cataloged PGs", len(all_records))
        s3.metric("State-wide Avg Rent", fmt_money(df_listings["rent"].mean() if not df_listings.empty else 0))

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # 3-column card grid
        cols = st.columns(3)
        for i, dist in enumerate(districts_to_show):
            # Lookup stats from summary
            stats_row = district_summary[district_summary["district"] == dist]
            if not stats_row.empty:
                count_val = int(stats_row.iloc[0]["total_listings"])
                avail_val = int(stats_row.iloc[0]["available_listings"])
                min_r = int(stats_row.iloc[0]["min_rent"])
                avg_r = int(stats_row.iloc[0]["avg_rent"])
            else:
                count_val, avail_val, min_r, avg_r = 0, 0, 0, 0

            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"#### 📍 {dist}")
                    st.markdown(
                        f"<div style='font-size: 0.86rem; color: #475569; margin-bottom: 8px;'>"
                        f"Listings: <strong>{count_val}</strong> · Available: <strong style='color:#059669;'>{avail_val}</strong><br>"
                        f"Avg Rent: <strong>{fmt_money(avg_r)}</strong> · From: <strong>{fmt_money(min_r)}</strong>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    if st.button(f"Browse {dist} PGs", key=f"btn_explore_{dist}", use_container_width=True):
                        st.session_state.selected_explore_district = dist
                        st.rerun()

# ---------------------------------------------------------
# View 4: Compare PGs Side-by-Side
# ---------------------------------------------------------
elif st.session_state.page == "Compare PGs":
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <h1 style="margin: 0; font-size: 2.1rem;">Compare Accommodations</h1>
        <p style="color: #64748b; font-size: 1rem; margin-top: 4px;">
            Compare rent, facilities, sharing types, and amenities side-by-side to make the best decision.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Multi-select options
    options_map = {f"#{int(r['id'])} · {r['name']} ({r['district']}) — {fmt_money(r['rent'])}": int(r['id']) for r in all_records}

    # Selected listing ids
    selected_labels = [k for k, v in options_map.items() if v in st.session_state.compare_ids]
    chosen_labels = st.multiselect("Choose 2 to 4 PGs to compare:", list(options_map.keys()), default=selected_labels, max_selections=4)

    # Update compare queue
    st.session_state.compare_ids = [options_map[lbl] for lbl in chosen_labels]

    if len(st.session_state.compare_ids) >= 2:
        comp_df = df_listings[df_listings["id"].isin(st.session_state.compare_ids)].copy()

        # Clean compare table
        st.markdown("### ⚖️ Side-by-Side Comparison Matrix")

        fields = [
            ("Monthly Rent", lambda r: fmt_money(r["rent"])),
            ("Security Deposit", lambda r: fmt_money(r.get("deposit", 0))),
            ("District", lambda r: str(r["district"])),
            ("City & Locality", lambda r: f"{r['locality']}, {r['city']}"),
            ("Sharing Type", lambda r: str(r["sharing"])),
            ("Accommodation Type", lambda r: str(r["gender_policy"])),
            ("Food Availability", lambda r: str(r.get("food", "Not specified"))),
            ("Food / Meal Details", lambda r: str(r.get("food_meals") or "Not specified")),
            ("Availability", lambda r: "🟢 Available" if int(r.get("vacancy", 0)) else "🔴 Occupied"),
            ("Distance to Hub", lambda r: f"{float(r.get('distance_km', 0) or 0):g} km"),
            ("Amenities", lambda r: str(r.get("amenities", ""))),
            ("Contact Number", lambda r: str(r.get("contact") or "Available on request"))
        ]

        # Render Header Columns
        header_cols = st.columns(len(comp_df) + 1)
        header_cols[0].markdown("**Feature**")
        for idx, (_, r) in enumerate(comp_df.iterrows()):
            header_cols[idx + 1].markdown(f"**{r['name']}**")

        st.divider()

        # Render Data Rows
        for label, extractor in fields:
            row_cols = st.columns(len(comp_df) + 1)
            row_cols[0].markdown(f"**{label}**")
            for idx, (_, r) in enumerate(comp_df.iterrows()):
                val = extractor(r)
                row_cols[idx + 1].write(val)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        if st.button("Clear Comparison Queue"):
            st.session_state.compare_ids = []
            st.rerun()

    else:
        st.info("👉 Select at least 2 accommodations to see the side-by-side comparison table.")

# ---------------------------------------------------------
# View 5: Saved Listings & Search History
# ---------------------------------------------------------
elif st.session_state.page == "Saved & History":
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <h1 style="margin: 0; font-size: 2.1rem;">Saved Listings & Search History</h1>
        <p style="color: #64748b; font-size: 1rem; margin-top: 4px;">
            Access your bookmarked PGs and past search filters for quick re-application.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_saved, tab_history = st.tabs(["❤️ Saved Accommodations", "🕒 Past Search History"])

    with tab_saved:
        saved_df = get_saved_listings(uid)
        if saved_df.empty:
            st.markdown("""
            <div style="text-align: center; padding: 40px 20px; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0;">
                <div style="font-size: 3rem; margin-bottom: 8px;">🤍</div>
                <h3 style="margin: 0; color: #1e3a8a;">No Saved Listings Yet</h3>
                <p style="color: #64748b; max-width: 440px; margin: 6px auto 18px auto;">
                    While exploring or searching for PGs, click the heart button to save your favorites here.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"#### You have saved {len(saved_df)} accommodation(s):")
            for _, r in saved_df.iterrows():
                render_pg_card(r, context_key="saved_view")

    with tab_history:
        history_df = get_search_history(uid)
        if history_df.empty:
            st.info("No past searches recorded yet. Search filters applied in the Smart PG Finder will be saved here.")
        else:
            h_col1, h_col2 = st.columns([3, 1])
            with h_col1:
                st.markdown(f"#### Recent Searches ({len(history_df)}):")
            with h_col2:
                if st.button("Clear Search History", use_container_width=True):
                    clear_all_search_history(uid)
                    st.rerun()

            for _, h in history_df.iterrows():
                try:
                    f_data = json.loads(h["filters_json"])
                except Exception:
                    f_data = {}

                with st.container(border=True):
                    hc1, hc2 = st.columns([3, 1])
                    with hc1:
                        st.markdown(f"**District:** {f_data.get('district', 'All')} · **Budget:** {fmt_money(f_data.get('min_budget',0))} – {fmt_money(f_data.get('max_budget',0))}")
                        st.caption(f"Sharing: {f_data.get('sharing', 'Any')} · Food: {f_data.get('food', 'Any')} · AC: {f_data.get('ac_type', 'Any')} · Results Found: {h['result_count']}")
                        st.caption(f"Searched on: {h['created_at']}")
                    with hc2:
                        if st.button("Re-run Search", key=f"rerun_{h['id']}", use_container_width=True):
                            st.session_state.last_search_prefs = f_data
                            st.session_state.last_search_results = recommend_listings(all_records, f_data)
                            st.session_state.page = "Smart PG Finder"
                            st.rerun()

# ---------------------------------------------------------
# View 6: Analytics Dashboard
# ---------------------------------------------------------
elif st.session_state.page == "Analytics Dashboard":
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <h1 style="margin: 0; font-size: 2.1rem;">StayMatch Analytics Dashboard</h1>
        <p style="color: #64748b; font-size: 1rem; margin-top: 4px;">
            Real-time market insights and distribution metrics across Tamil Nadu PG accommodations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if df_listings.empty:
        st.info("Add accommodations to generate analytics.")
    else:
        # Top KPI cards
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Listings", len(df_listings))
        k2.metric("Available Rooms", int(df_listings["vacancy"].sum()))
        k3.metric("Districts Active", df_listings["district"].nunique())
        avg_r = df_listings.loc[df_listings["vacancy"] == 1, "rent"].mean()
        k4.metric("Avg Monthly Rent", fmt_money(avg_r if not pd.isna(avg_r) else 0))

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Charts Row 1: District PG Distribution
        dist_counts = df_listings.groupby("district").size().reset_index(name="Listings").sort_values("Listings", ascending=False)
        fig_dist = px.bar(
            dist_counts,
            x="district",
            y="Listings",
            color="Listings",
            color_continuous_scale="Blues",
            title="Tamil Nadu District-wise PG Distribution",
            labels={"district": "District", "Listings": "Total PG Listings"},
            height=380
        )
        fig_dist.update_layout(margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="#ffffff")
        st.plotly_chart(fig_dist, use_container_width=True)

        # Charts Row 2: Rent Analysis & Accommodation Type Share
        c_left, c_right = st.columns(2)
        with c_left:
            avg_rent_dist = df_listings.groupby("district", as_index=False)["rent"].mean().sort_values("rent", ascending=False).head(15)
            fig_rent = px.bar(
                avg_rent_dist,
                x="district",
                y="rent",
                color="rent",
                color_continuous_scale="Teal",
                title="Top 15 Districts by Average Monthly Rent (₹)",
                labels={"district": "District", "rent": "Average Rent (₹)"},
                height=360
            )
            fig_rent.update_layout(margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="#ffffff")
            st.plotly_chart(fig_rent, use_container_width=True)

        with c_right:
            fig_policy = px.pie(
                df_listings,
                names="gender_policy",
                hole=0.55,
                color_discrete_sequence=["#1e40af", "#3b82f6", "#93c5fd"],
                title="Accommodation Type Distribution (Co-living / Boys / Girls)",
                height=360
            )
            fig_policy.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_policy, use_container_width=True)

        # Charts Row 3: Sharing Types & Budget Brackets
        c_left2, c_right2 = st.columns(2)
        with c_left2:
            fig_share = px.pie(
                df_listings,
                names="sharing",
                hole=0.55,
                color_discrete_sequence=["#0f766e", "#0d9488", "#14b8a6", "#2dd4bf", "#99f6e4"],
                title="Sharing Preferences Distribution",
                height=360
            )
            fig_share.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_share, use_container_width=True)

        with c_right2:
            bins = [0, 5000, 8000, 12000, 18000, 1000000]
            bin_labels = ["≤ ₹5,000", "₹5,001–₹8,000", "₹8,001–₹12,000", "₹12,001–₹18,000", "> ₹18,000"]
            b_df = df_listings.copy()
            b_df["Budget Range"] = pd.cut(b_df["rent"], bins=bins, labels=bin_labels, include_lowest=True)
            budget_counts = b_df.groupby("Budget Range", observed=False).size().reset_index(name="Count")

            fig_budget = px.bar(
                budget_counts,
                x="Budget Range",
                y="Count",
                color="Count",
                color_continuous_scale="Purples",
                title="Accommodation Distribution Across Budget Brackets",
                labels={"Count": "Listings"},
                height=360
            )
            fig_budget.update_layout(margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="#ffffff")
            st.plotly_chart(fig_budget, use_container_width=True)

        # Amenity Prevalence Chart
        st.markdown("### 🛠️ Facility & Amenity Availability Rate")
        amenity_counts = {a: 0 for a in AMENITIES}
        for _, r in df_listings.iterrows():
            ams = parse_amenities(r.get("amenities", ""))
            for a in AMENITIES:
                if a.lower() in ams or ("ro water" in ams and a == "RO Water"):
                    amenity_counts[a] += 1

        df_am = pd.DataFrame([
            {"Facility": k, "Percentage": round((v / len(df_listings)) * 100, 1)}
            for k, v in amenity_counts.items()
        ]).sort_values("Percentage", ascending=False)

        fig_am = px.bar(
            df_am,
            x="Facility",
            y="Percentage",
            text="Percentage",
            color="Percentage",
            color_continuous_scale="Blues",
            title="Percentage of Tamil Nadu PGs Offering Each Facility (%)",
            labels={"Percentage": "% of PGs"},
            height=360
        )
        fig_am.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_am.update_layout(margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="#ffffff", yaxis_range=[0, 110])
        st.plotly_chart(fig_am, use_container_width=True)

# ---------------------------------------------------------
# View 7: Listing Management (Admin)
# ---------------------------------------------------------
elif st.session_state.page == "Listing Management":
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <h1 style="margin: 0; font-size: 2.1rem;">PG Listing Management</h1>
        <p style="color: #64748b; font-size: 1rem; margin-top: 4px;">
            Create, update, and manage accommodation records stored securely in your SQLite database.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_add, tab_edit = st.tabs(["➕ Add New PG Listing", "✏️ Manage / Edit Existing Listings"])

    with tab_add:
        with st.form("add_pg_listing_form", clear_on_submit=True):
            st.markdown("#### Create New Listing Record")
            c1, c2 = st.columns(2)

            with c1:
                new_name = st.text_input("Property / PG Name *", placeholder="e.g. Royal Comforts PG")
                new_district = st.selectbox("Tamil Nadu District *", TAMIL_NADU_DISTRICTS)
                new_city = st.text_input("City", placeholder="e.g. Chennai / Coimbatore")
                new_locality = st.text_input("Locality / Landmark *", placeholder="e.g. Velachery / T. Nagar")
                new_rent = st.number_input("Monthly Rent (₹) *", min_value=500, max_value=300000, value=7500, step=500)
                new_deposit = st.number_input("Security Deposit (₹)", min_value=0, max_value=500000, value=15000, step=1000)
                new_sharing = st.selectbox("Sharing Option", SHARING_OPTIONS, index=1)

            with c2:
                new_gender = st.selectbox("Accommodation Type", ["Co-living", "Boys PG", "Girls PG"])
                new_food = st.selectbox("Food Provision", ["Included", "Not included", "Optional"])
                new_meals = st.text_input("Meals Details", placeholder="e.g. Breakfast, lunch and dinner on all days")
                new_amenities = st.multiselect("Facilities Available", AMENITIES, default=["Wi-Fi", "RO Water"])
                new_available = st.checkbox("Currently Available for Move-In", value=True)
                new_contact = st.text_input("Contact Number", placeholder="e.g. 9876543210")
                new_distance = st.number_input("Distance to City Hub/College (km)", min_value=0.0, max_value=100.0, value=1.5, step=0.5)

            new_desc = st.text_area("Accommodation Description", placeholder="Mention room size, ventilation, cleaning schedule...")
            new_rules = st.text_area("House Rules & Timings", placeholder="Gate closing time, visitor policy, smoking rules...")
            new_img = st.text_input("Custom Image URL (Optional)", placeholder="https://example.com/pg-photo.jpg")

            submit_add = st.form_submit_button("💾 Save PG Listing to Database", type="primary", use_container_width=True)

        if submit_add:
            if not new_name.strip() or not new_locality.strip():
                st.error("PG Name and Locality are mandatory fields.")
            elif new_rent <= 0:
                st.error("Monthly rent must be a positive amount.")
            else:
                new_record_data = {
                    "name": new_name.strip(),
                    "district": new_district,
                    "city": new_city.strip() or new_district,
                    "locality": new_locality.strip(),
                    "rent": int(new_rent),
                    "deposit": int(new_deposit),
                    "sharing": new_sharing,
                    "food": new_food,
                    "amenities": ", ".join(new_amenities),
                    "vacancy": 1 if new_available else 0,
                    "gender_policy": new_gender,
                    "contact": new_contact.strip(),
                    "description": new_desc.strip(),
                    "source_type": "User submitted",
                    "verified": 0,
                    "image_url": new_img.strip(),
                    "rules": new_rules.strip(),
                    "food_meals": new_meals.strip(),
                    "distance_km": float(new_distance)
                }
                new_id = add_listing(new_record_data)
                st.success(f"Listing '#{new_id} · {new_name}' created successfully and saved to SQLite!")
                st.rerun()

    with tab_edit:
        if df_listings.empty:
            st.info("No listings currently available in the database.")
        else:
            listing_choices = df_listings.apply(lambda r: f"#{int(r['id'])} · {r['name']} ({r['district']})", axis=1).tolist()
            chosen_item_label = st.selectbox("Select Listing to Edit or Remove:", listing_choices)
            chosen_lid = int(chosen_item_label.split(" · ")[0][1:])
            edit_item = get_listing(chosen_lid)

            if edit_item:
                with st.form("edit_pg_listing_form"):
                    st.markdown(f"#### Edit Details for: {edit_item['name']}")
                    ec1, ec2 = st.columns(2)

                    with ec1:
                        e_name = st.text_input("Property / PG Name", value=edit_item["name"])
                        e_district = st.selectbox("District", TAMIL_NADU_DISTRICTS, index=TAMIL_NADU_DISTRICTS.index(edit_item["district"]) if edit_item["district"] in TAMIL_NADU_DISTRICTS else 0)
                        e_city = st.text_input("City", value=edit_item.get("city", edit_item["district"]))
                        e_locality = st.text_input("Locality", value=edit_item["locality"])
                        e_rent = st.number_input("Monthly Rent (₹)", min_value=0, max_value=300000, value=int(edit_item["rent"]), step=500)
                        e_deposit = st.number_input("Security Deposit (₹)", min_value=0, max_value=500000, value=int(edit_item.get("deposit", 0)), step=1000)
                        e_sharing = st.selectbox("Sharing", SHARING_OPTIONS, index=SHARING_OPTIONS.index(edit_item["sharing"]) if edit_item["sharing"] in SHARING_OPTIONS else 0)

                    with ec2:
                        e_gender = st.selectbox("Type", ["Co-living", "Boys PG", "Girls PG"], index=["Co-living", "Boys PG", "Girls PG"].index(edit_item["gender_policy"]) if edit_item["gender_policy"] in ["Co-living", "Boys PG", "Girls PG"] else 0)
                        e_food = st.selectbox("Food", ["Included", "Not included", "Optional"], index=["Included", "Not included", "Optional"].index(edit_item["food"]) if edit_item["food"] in ["Included", "Not included", "Optional"] else 0)
                        e_meals = st.text_input("Meals Schedule", value=edit_item.get("food_meals", ""))
                        e_amenities = st.text_input("Amenities (comma separated)", value=edit_item.get("amenities", ""))
                        e_available = st.checkbox("Available Now", value=bool(edit_item.get("vacancy", 1)))
                        e_contact = st.text_input("Contact", value=edit_item.get("contact", ""))
                        e_distance = st.number_input("Distance (km)", min_value=0.0, max_value=100.0, value=float(edit_item.get("distance_km", 0.0) or 0.0), step=0.5)

                    e_desc = st.text_area("Description", value=edit_item.get("description", ""))
                    e_rules = st.text_area("Rules", value=edit_item.get("rules", ""))
                    e_img = st.text_input("Image URL", value=edit_item.get("image_url", ""))

                    submit_update = st.form_submit_button("Update Listing", type="primary", use_container_width=True)

                if submit_update:
                    update_payload = {
                        "name": e_name.strip(),
                        "district": e_district,
                        "city": e_city.strip() or e_district,
                        "locality": e_locality.strip(),
                        "rent": int(e_rent),
                        "deposit": int(e_deposit),
                        "sharing": e_sharing,
                        "food": e_food,
                        "amenities": e_amenities.strip(),
                        "vacancy": 1 if e_available else 0,
                        "gender_policy": e_gender,
                        "contact": e_contact.strip(),
                        "description": e_desc.strip(),
                        "image_url": e_img.strip(),
                        "rules": e_rules.strip(),
                        "food_meals": e_meals.strip(),
                        "distance_km": float(e_distance)
                    }
                    update_listing(chosen_lid, update_payload)
                    st.success("Listing updated successfully!")
                    st.rerun()

                st.markdown("---")
                st.markdown("##### ⚠️ Danger Zone")
                if st.button(f"🗑️ Permanently Delete Listing #{chosen_lid}", type="secondary"):
                    delete_listing(chosen_lid)
                    st.warning(f"Listing #{chosen_lid} has been deleted.")
                    st.rerun()

# ---------------------------------------------------------
# View: Fallback to Details
# ---------------------------------------------------------
elif st.session_state.page == "PG details":
    render_details_page()

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.84rem; padding: 20px 0; border-top: 1px solid #e2e8f0;">
    <strong>StayMatch — Smart PG Finder & Recommendation System</strong> · Designed for Tamil Nadu College Students & Working Professionals<br>
    Built with Python, Streamlit, SQLite & Plotly · Production & Presentation Ready
</div>
""", unsafe_allow_html=True)
