"""Streamlit Dashboard for Know Your Agent - AI Agent Trust & Fraud Detection Layer.
Theme: 25+ Shades of Burgundy Edition (Dusty Rose to Deep Berry Velvet) 🍷
"""

import os
import time
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Know Your Agent | Burgundy Trust Inspector",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL configuration - Defaults to live production Render URL
API_BASE_URL = os.getenv("API_BASE_URL", "https://know-your-agent.onrender.com")

# Custom Burgundy Palette CSS Injector (Matching 25+ Shades Palette)
# Shades: #FBF2F4 (Soft Mauve Light), #F5E6E9 (Rose Cream), #E8ADB8 (Dusty Rose), 
# #C56B7B (Medium Rose), #A03C4F (Berry Burgundy), #801B2C (Deep Wine Burgundy), #5E0B1B (Rich Maroon)
BURGUNDY_CSS = """
<style>
    /* Global Light & Elegant Page Background */
    .stApp {
        background-color: #FBF2F4;
        color: #2A080F;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #F5E6E9 !important;
        border-right: 1px solid #E8ADB8 !important;
    }
    
    /* Card Container Styling */
    .burgundy-card {
        background: #FFFFFF;
        border: 1px solid #E8ADB8;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 4px 15px rgba(128, 27, 44, 0.08);
    }
    
    .burgundy-card-header {
        color: #801B2C;
        font-weight: 700;
        font-size: 1.15rem;
        margin-bottom: 8px;
    }
    
    /* Metric Card Custom Styling */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E8ADB8;
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 3px 10px rgba(128, 27, 44, 0.06);
    }
    
    div[data-testid="stMetricLabel"] {
        color: #A03C4F !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    div[data-testid="stMetricValue"] {
        color: #5E0B1B !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }
    
    /* Custom Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #801B2C 0%, #A03C4F 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 12px rgba(128, 27, 44, 0.25) !important;
        transition: all 0.25s ease !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #A03C4F 0%, #C56B7B 100%) !important;
        box-shadow: 0 6px 16px rgba(160, 60, 79, 0.4) !important;
        transform: translateY(-1px);
    }
    
    /* Input Fields */
    input, select {
        background-color: #FFFFFF !important;
        color: #2A080F !important;
        border: 1px solid #E8ADB8 !important;
        border-radius: 6px !important;
    }
    
    /* Headers & Text */
    h1, h2, h3 {
        color: #5E0B1B !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    .stCaption {
        color: #801B2C !important;
    }
    
    /* Dataframe Styling */
    .stDataFrame {
        border: 1px solid #E8ADB8;
        border-radius: 10px;
    }
</style>
"""

st.markdown(BURGUNDY_CSS, unsafe_allow_html=True)


def fetch_stats():
    try:
        res = requests.get(f"{API_BASE_URL}/stats", timeout=4.0)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


def fetch_actions(flagged_only=False, agent_id=None, limit=100):
    try:
        params = {"limit": limit, "flagged_only": flagged_only}
        if agent_id:
            params["agent_id"] = agent_id
        res = requests.get(f"{API_BASE_URL}/actions", params=params, timeout=5.0)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


def fetch_audit_trail(action_id):
    try:
        res = requests.get(f"{API_BASE_URL}/audit/{action_id}", timeout=5.0)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


# Sidebar
st.sidebar.markdown("""
<div style="text-align: center; padding: 12px 0;">
    <h2 style="color: #5E0B1B; margin: 0; font-size: 1.6rem; font-weight: 800;">🍷 Know Your Agent</h2>
    <p style="color: #A03C4F; font-size: 0.85rem; margin-top: 4px; font-weight: 600;">Shades of Burgundy Palette Edition</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.divider()

# Sidebar Controls
auto_refresh = st.sidebar.checkbox("Auto Refresh (5s)", value=False)
flagged_filter = st.sidebar.checkbox("Filter Flagged Only", value=False)
agent_id_input = st.sidebar.text_input("Filter by Agent ID", "")
refresh_btn = st.sidebar.button("🔄 Refresh Stream", use_container_width=True)

st.sidebar.divider()
st.sidebar.markdown("<h4 style='color: #801B2C;'>⚡ Agent Traffic Generator</h4>", unsafe_allow_html=True)
sim_count = st.sidebar.number_input("Batch Size", min_value=5, max_value=100, value=25)
sim_anomaly_rate = st.sidebar.slider("Anomaly Inject Ratio", 0.0, 1.0, 0.25, 0.05)

if st.sidebar.button("🍷 Run Agent Simulation", use_container_width=True):
    with st.spinner("Executing burgundy trust evaluations on live server..."):
        try:
            from simulator.generator import AgentActionGenerator
            gen = AgentActionGenerator(anomaly_rate=sim_anomaly_rate)
            actions_batch = gen.generate_batch(count=sim_count)
            success_count = 0
            for act in actions_batch:
                r = requests.post(f"{API_BASE_URL}/score-action", json=act, timeout=4.0)
                if r.status_code == 201:
                    success_count += 1
            st.sidebar.success(f"Successfully processed {success_count} agent actions!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Simulation failed: {e}")

# Title Banner
st.markdown("""
<div style="background: linear-gradient(135deg, #801B2C 0%, #A03C4F 50%, #C56B7B 100%); padding: 24px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 6px 20px rgba(128, 27, 44, 0.25);">
    <h1 style="margin: 0; font-size: 2.3rem; color: #FFFFFF !important; font-weight: 800;">🍷 Know Your Agent — AI Trust & Fraud Layer</h1>
    <p style="margin: 8px 0 0 0; color: #FBF2F4; font-size: 1.05rem; font-weight: 500;">
        Isolation Forest Anomaly Scoring + Hard Rule Safeguards + SHAP Feature Explainability
    </p>
</div>
""", unsafe_allow_html=True)

# Top Metrics Row
stats = fetch_stats()

m1, m2, m3, m4, m5 = st.columns(5)
if stats:
    m1.metric("Total Actions", stats["total_actions"])
    m2.metric("Clean Actions", stats["clean_actions"])
    m3.metric("Flagged Actions", stats["flagged_actions"], delta=f"{stats['flag_rate_percentage']}% Flag Rate", delta_color="inverse")
    m4.metric("Avg Risk Score", f"{stats['average_risk_score']}/100")
    m5.metric("Critical / High", stats["high_risk_actions"])
else:
    st.warning(f"Connecting to live production backend at `{API_BASE_URL}`...")

st.markdown("<br>", unsafe_allow_html=True)

# Fetch Actions List
raw_actions = fetch_actions(flagged_only=flagged_filter, agent_id=agent_id_input if agent_id_input else None)

if not raw_actions:
    st.info("No actions recorded yet. Click **'🍷 Run Agent Simulation'** in the sidebar to generate live agent traffic!")
else:
    # Prepare DataFrame for Table
    table_data = []
    for item in raw_actions:
        act = item["action"]
        rs = item.get("risk_score") or {}

        score_val = rs.get("risk_score", 0.0)
        flagged_bool = rs.get("flagged", False)
        risk_lvl = rs.get("risk_level", "UNKNOWN")

        badge = "🟢 LOW"
        if risk_lvl == "MEDIUM":
            badge = "🟡 MEDIUM"
        elif risk_lvl == "HIGH":
            badge = "🟠 HIGH"
        elif risk_lvl == "CRITICAL":
            badge = "🍷 CRITICAL"

        table_data.append({
            "Action ID": act["id"],
            "Timestamp": act["timestamp"][:19].replace("T", " "),
            "Agent ID": act["agent_id"],
            "User ID": act["user_id"],
            "Action Type": act["action_type"],
            "Merchant": act["merchant_name"],
            "New Merchant": "⚠️ Yes" if act["is_new_merchant"] else "No",
            "Amount ($)": f"${act['amount']:.2f}",
            "Risk Score": score_val,
            "Risk Level": badge,
            "Flagged": "❌ FLAGGED" if flagged_bool else "✅ CLEAN"
        })

    df_actions = pd.DataFrame(table_data)

    # Main Grid Layout: Left Stream + Right Inspector
    col_left, col_right = st.columns([1.25, 1.0])

    with col_left:
        st.subheader("📋 Agent Action Stream")

        st.dataframe(
            df_actions[["Timestamp", "Agent ID", "Action Type", "Merchant", "Amount ($)", "Risk Score", "Risk Level", "Flagged"]],
            use_container_width=True,
            height=380
        )

        # Burgundy Palette Timeline Chart
        st.subheader("📈 Risk Score Timeline")

        df_actions["Timestamp_dt"] = pd.to_datetime(df_actions["Timestamp"])
        fig_scatter = px.scatter(
            df_actions,
            x="Timestamp_dt",
            y="Risk Score",
            color="Flagged",
            size=df_actions["Risk Score"].clip(lower=12),
            hover_data=["Agent ID", "Merchant", "Amount ($)"],
            color_discrete_map={"❌ FLAGGED": "#801B2C", "✅ CLEAN": "#2E7D32"},
            title="Action Risk Timeline (Dusty Rose & Berry Highlights)"
        )
        fig_scatter.add_hline(y=50.0, line_dash="dash", line_color="#A03C4F", annotation_text="Flag Threshold (50.0)")
        fig_scatter.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FBF2F4",
            font=dict(color="#2A080F"),
            height=320,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_right:
        st.subheader("🔍 Action Inspector & SHAP Breakdown")

        action_ids = [item["action"]["id"] for item in raw_actions]
        selected_action_id = st.selectbox(
            "Select an Action ID to inspect SHAP explanation:",
            options=action_ids,
            format_func=lambda aid: f"{aid[:8]}... | ${next(i['action']['amount'] for i in raw_actions if i['action']['id']==aid):.2f} | {next(i['action']['merchant_name'] for i in raw_actions if i['action']['id']==aid)}"
        )

        if selected_action_id:
            audit_detail = fetch_audit_trail(selected_action_id)
            if audit_detail:
                act = audit_detail["action"]
                rs = audit_detail.get("risk_score")

                # Action Header Card
                st.markdown(f"""
                <div class="burgundy-card">
                    <div class="burgundy-card-header">Action: {act['action_type'].upper()} → {act['merchant_name']}</div>
                    <p style="margin: 0; color: #2A080F; font-size: 0.95rem;">
                        <b>Agent:</b> <span style="color: #801B2C; font-weight: 700;">{act['agent_id']}</span> | <b>User:</b> {act['user_id']} <br>
                        <b>Amount:</b> <span style="font-size: 1.35em; font-weight: 800; color: #801B2C;">${act['amount']:.2f} {act['currency']}</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if rs:
                    score = rs["risk_score"]
                    flagged = rs["flagged"]
                    shap_data = rs.get("shap_explanation", {})

                    # Burgundy Palette Risk Gauge Chart
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=score,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': f"Risk Score ({rs['risk_level']})", 'font': {'size': 18, 'color': "#801B2C"}},
                        gauge={
                            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#A03C4F"},
                            'bar': {'color': "#801B2C" if flagged else "#2E7D32"},
                            'steps': [
                                {'range': [0, 30], 'color': "rgba(46, 125, 50, 0.12)"},
                                {'range': [30, 55], 'color': "rgba(245, 158, 11, 0.15)"},
                                {'range': [55, 100], 'color': "rgba(128, 27, 44, 0.20)"}
                            ],
                            'threshold': {
                                'line': {'color': "#A03C4F", 'width': 4},
                                'thickness': 0.75,
                                'value': 50
                            }
                        }
                    ))
                    fig_gauge.update_layout(
                        paper_bgcolor="#FFFFFF",
                        font=dict(color="#2A080F"),
                        height=210,
                        margin=dict(l=20, r=20, t=30, b=10)
                    )
                    st.plotly_chart(fig_gauge, use_container_width=True)

                    # Summary Reasons
                    st.markdown("<h5 style='color: #801B2C;'>💡 Key Risk Drivers (Rules & SHAP)</h5>", unsafe_allow_html=True)
                    reasons = shap_data.get("summary_reasons", [])
                    for reason in reasons:
                        st.markdown(f"- <span style='color: #5E0B1B; font-weight: 600;'>{reason}</span>", unsafe_allow_html=True)

                    # Burgundy Palette SHAP Bar Chart
                    st.markdown("<h5 style='color: #801B2C;'>📊 SHAP Feature Attribution Impact</h5>", unsafe_allow_html=True)
                    impacts = shap_data.get("feature_impacts", [])
                    if impacts:
                        df_shap = pd.DataFrame(impacts)
                        fig_shap = px.bar(
                            df_shap,
                            x="contribution_pts",
                            y="feature",
                            orientation="h",
                            color="contribution_pts",
                            color_continuous_scale=["#F5E6E9", "#E8ADB8", "#C56B7B", "#A03C4F", "#801B2C", "#5E0B1B"],
                            text="contribution_pts",
                            labels={"contribution_pts": "Risk Points Added", "feature": "Feature"},
                            title="SHAP Feature Contribution"
                        )
                        fig_shap.update_layout(
                            paper_bgcolor="#FFFFFF",
                            plot_bgcolor="#FBF2F4",
                            font=dict(color="#2A080F"),
                            height=260,
                            margin=dict(l=10, r=10, t=35, b=10)
                        )
                        st.plotly_chart(fig_shap, use_container_width=True)

                    # Triggered Rules Details
                    rules = rs.get("rule_flags", [])
                    if rules:
                        st.markdown("<h5 style='color: #801B2C;'>🚨 Triggered Hard Rules</h5>", unsafe_allow_html=True)
                        for r in rules:
                            st.warning(f"**[{r['severity']}] {r['rule_name']}**: {r['description']} (+{r['points']} pts)")

                # Raw Metadata Expander
                with st.expander("🛠️ Raw JSON Payload & Audit Log"):
                    st.json(audit_detail)

if auto_refresh:
    time.sleep(5)
    st.rerun()
