"""Streamlit Dashboard for Know Your Agent - AI Agent Trust & Fraud Detection Layer."""

import os
import time
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Know Your Agent | Trust & Fraud Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def fetch_stats():
    try:
        res = requests.get(f"{API_BASE_URL}/stats", timeout=3.0)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


def fetch_actions(flagged_only=False, agent_id=None, limit=100):
    try:
        params = {"limit": limit, "flagged_only": flagged_only}
        if agent_id:
            params["agent_id"] = agent_id
        res = requests.get(f"{API_BASE_URL}/actions", params=params, timeout=4.0)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


def fetch_audit_trail(action_id):
    try:
        res = requests.get(f"{API_BASE_URL}/audit/{action_id}", timeout=4.0)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


# Sidebar
st.sidebar.image("https://img.icons8.com/isometric-folders/100/security-pass.png", width=70)
st.sidebar.title("Know Your Agent")
st.sidebar.markdown("**AI Agent Trust & Fraud Layer**")
st.sidebar.divider()

# Sidebar Controls
auto_refresh = st.sidebar.checkbox("Auto Refresh (5s)", value=False)
flagged_filter = st.sidebar.checkbox("Filter Flagged Only", value=False)
agent_id_input = st.sidebar.text_input("Filter by Agent ID", "")
refresh_btn = st.sidebar.button("🔄 Refresh Now", use_container_width=True)

st.sidebar.divider()
st.sidebar.subheader("🚀 Simulation Controller")
sim_count = st.sidebar.number_input("Actions to simulate", min_value=5, max_value=100, value=25)
sim_anomaly_rate = st.sidebar.slider("Anomaly Rate", 0.0, 1.0, 0.25, 0.05)

if st.sidebar.button("⚡ Trigger Simulation Run", use_container_width=True):
    with st.spinner("Generating and scoring agent traffic..."):
        try:
            from simulator.generator import AgentActionGenerator
            gen = AgentActionGenerator(anomaly_rate=sim_anomaly_rate)
            actions_batch = gen.generate_batch(count=sim_count)
            success_count = 0
            for act in actions_batch:
                r = requests.post(f"{API_BASE_URL}/score-action", json=act, timeout=3.0)
                if r.status_code == 201:
                    success_count += 1
            st.sidebar.success(f"Simulated {success_count} agent actions!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Simulation failed: {e}")

# Header Title
st.title("🛡️ Know Your Agent — Trust & Fraud Inspector")
st.caption("Real-time Isolation Forest ML + Rule-Based Anomaly Scoring with SHAP Explainability for AI Payment Agents")

# Top Metrics Row
stats = fetch_stats()

m1, m2, m3, m4, m5 = st.columns(5)
if stats:
    m1.metric("Total Actions", stats["total_actions"])
    m2.metric("Clean Actions", stats["clean_actions"])
    m3.metric("Flagged Actions", stats["flagged_actions"], delta=f"{stats['flag_rate_percentage']}% Flag Rate", delta_color="inverse")
    m4.metric("Avg Risk Score", f"{stats['average_risk_score']}/100")
    m5.metric("High/Critical Risk", stats["high_risk_actions"])
else:
    st.warning(f"Unable to connect to FastAPI backend at `{API_BASE_URL}`. Ensure backend is running!")

st.divider()

# Fetch Actions List
raw_actions = fetch_actions(flagged_only=flagged_filter, agent_id=agent_id_input if agent_id_input else None)

if not raw_actions:
    st.info("No actions recorded yet. Use the sidebar **Simulation Controller** to generate synthetic agent transactions!")
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
            badge = "🔴 CRITICAL"

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

    # Main Grid Layout: Left Table + Right Timeline/Inspector
    col_left, col_right = st.columns([1.2, 1.0])

    with col_left:
        st.subheader("📋 Agent Action Stream")

        # Color highlight styled dataframe
        st.dataframe(
            df_actions[["Timestamp", "Agent ID", "Action Type", "Merchant", "Amount ($)", "Risk Score", "Risk Level", "Flagged"]],
            use_container_width=True,
            height=400
        )

        # Timeline Chart
        st.subheader("📈 Risk Score Distribution & Timeline")

        df_actions["Timestamp_dt"] = pd.to_datetime(df_actions["Timestamp"])
        fig_scatter = px.scatter(
            df_actions,
            x="Timestamp_dt",
            y="Risk Score",
            color="Flagged",
            size=df_actions["Risk Score"].clip(lower=10),
            hover_data=["Agent ID", "Merchant", "Amount ($)"],
            color_discrete_map={"❌ FLAGGED": "#ef4444", "✅ CLEAN": "#10b981"},
            title="Real-Time Risk Scores (Red = Flagged for Human Review)"
        )
        fig_scatter.add_hline(y=50.0, line_dash="dash", line_color="orange", annotation_text="Flag Threshold (50.0)")
        fig_scatter.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
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
                <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #f8fafc;">Action: {act['action_type'].upper()} to {act['merchant_name']}</h4>
                    <p style="margin: 5px 0 0 0; color: #94a3b8;">
                        <b>Agent:</b> {act['agent_id']} | <b>User:</b> {act['user_id']} | <b>Amount:</b> <span style="font-size: 1.2em; color: #38bdf8;">${act['amount']:.2f} {act['currency']}</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if rs:
                    score = rs["risk_score"]
                    flagged = rs["flagged"]
                    shap_data = rs.get("shap_explanation", {})

                    # Risk Gauge Chart
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=score,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': f"Risk Score ({rs['risk_level']})", 'font': {'size': 18}},
                        gauge={
                            'axis': {'range': [0, 100], 'tickwidth': 1},
                            'bar': {'color': "#ef4444" if flagged else "#10b981"},
                            'steps': [
                                {'range': [0, 30], 'color': "rgba(16, 185, 129, 0.2)"},
                                {'range': [30, 55], 'color': "rgba(245, 158, 11, 0.2)"},
                                {'range': [55, 100], 'color': "rgba(239, 68, 68, 0.2)"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 50
                            }
                        }
                    ))
                    fig_gauge.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=10))
                    st.plotly_chart(fig_gauge, use_container_width=True)

                    # Summary Reasons
                    st.markdown("##### 💡 Key Risk Drivers (SHAP Attribution & Rules)")
                    reasons = shap_data.get("summary_reasons", [])
                    for reason in reasons:
                        st.markdown(f"- {reason}")

                    # SHAP Feature Attribution Bar Chart
                    st.markdown("##### 📊 SHAP Feature Contributions (Risk Points Added)")
                    impacts = shap_data.get("feature_impacts", [])
                    if impacts:
                        df_shap = pd.DataFrame(impacts)
                        fig_shap = px.bar(
                            df_shap,
                            x="contribution_pts",
                            y="feature",
                            orientation="h",
                            color="contribution_pts",
                            color_continuous_scale="Reds",
                            text="contribution_pts",
                            labels={"contribution_pts": "Risk Points Impact", "feature": "Feature"},
                            title="Feature Attribution Breakdown"
                        )
                        fig_shap.update_layout(height=260, margin=dict(l=10, r=10, t=35, b=10))
                        st.plotly_chart(fig_shap, use_container_width=True)

                    # Triggered Rules Details
                    rules = rs.get("rule_flags", [])
                    if rules:
                        st.markdown("##### 🚨 Triggered Hard Rules")
                        for r in rules:
                            st.warning(f"**[{r['severity']}] {r['rule_name']}**: {r['description']} (+{r['points']} pts)")

                # Raw Metadata Expander
                with st.expander("🛠️ Raw JSON Payload & Audit Log"):
                    st.json(audit_detail)

if auto_refresh:
    time.sleep(5)
    st.rerun()
