"""Telecom 360° — Real-Time Operations & Executive Analytics Dashboard.

Provides executive visibility, network NOC telemetry, and Customer 360 drill-down.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Set Page Config
st.set_page_config(
    page_title="Telecom 360° Platform",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Dark Glassmorphism Theme)
st.markdown("""
<style>
    .main {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-subtitle {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 4px;
    }
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.2);
        color: #f87171;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-high {
        background-color: rgba(249, 115, 22, 0.2);
        color: #fb923c;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-medium {
        background-color: rgba(234, 179, 8, 0.2);
        color: #facc15;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_gold_data():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gold_dir = os.path.join(base, "data", "gold")

    c360_path = os.path.join(gold_dir, "customer_360.parquet")
    net_path = os.path.join(gold_dir, "network_health.parquet")
    inc_path = os.path.join(gold_dir, "network_incidents.parquet")
    rev_path = os.path.join(gold_dir, "revenue_summary.parquet")
    pred_path = os.path.join(gold_dir, "customer_churn_predictions.parquet")

    c360 = pd.read_parquet(c360_path) if os.path.exists(c360_path) else pd.DataFrame()
    net = pd.read_parquet(net_path) if os.path.exists(net_path) else pd.DataFrame()
    inc = pd.read_parquet(inc_path) if os.path.exists(inc_path) else pd.DataFrame()
    rev = pd.read_parquet(rev_path) if os.path.exists(rev_path) else pd.DataFrame()
    pred = pd.read_parquet(pred_path) if os.path.exists(pred_path) else pd.DataFrame()

    return c360, net, inc, rev, pred


c360_df, net_df, inc_df, rev_df, pred_df = load_gold_data()

# Sidebar Navigation & Controls
st.sidebar.image("https://img.icons8.com/isometric/100/satellite-sending-signal.png", width=64)
st.sidebar.title("Telecom 360°")
st.sidebar.caption("Real-Time Lakehouse Platform")

menu = st.sidebar.radio(
    "Navigation",
    ["📊 Executive Overview", "📡 Network Operations & NOC", "👤 Customer 360 & Churn", "🏗️ Architecture & Pipeline"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Data Lakehouse Status**")
st.sidebar.success("● Bronze Layer: Active")
st.sidebar.success("● Silver Layer: Cleaned & SCD2")
st.sidebar.success("● Gold Marts: Synced")
st.sidebar.info("● ML Engine: XGBoost Active")

# -------------------------------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# -------------------------------------------------------------------------------------------------
if menu == "📊 Executive Overview":
    st.title("Executive Leadership Overview")
    st.markdown("High-level key performance indicators, subscriber growth, and monthly revenue performance.")

    # Top Metric Cards
    total_cust = len(c360_df) if not c360_df.empty else 0
    total_rev = rev_df["total_revenue"].iloc[0] if not rev_df.empty else 0.0
    arpu = rev_df["arpu"].iloc[0] if not rev_df.empty else 0.0
    active_incidents = len(inc_df) if not inc_df.empty else 0
    high_churn_rate = (pred_df["risk_tier"] == "HIGH").mean() * 100 if not pred_df.empty else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Active Subscribers</div>
            <div class="metric-value">{total_cust:,}</div>
            <div class="metric-subtitle">Across 5 Geographic Regions</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Monthly Revenue</div>
            <div class="metric-value">${total_rev:,.2f}</div>
            <div class="metric-subtitle">Billed Total</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">ARPU</div>
            <div class="metric-value">${arpu:.2f}</div>
            <div class="metric-subtitle">Avg Revenue Per User</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Network Incidents</div>
            <div class="metric-value" style="color: {'#ef4444' if active_incidents > 0 else '#22c55e'}">{active_incidents}</div>
            <div class="metric-subtitle">SLA Breaches Detected</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">High Churn Risk</div>
            <div class="metric-value" style="color: #f97316">{high_churn_rate:.1f}%</div>
            <div class="metric-subtitle">Prioritized Retention Watchlist</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    row1_c1, row1_c2 = st.columns([3, 2])
    with row1_c1:
        st.subheader("Subscription Tier Distribution")
        if not c360_df.empty and "plan_name" in c360_df.columns:
            plan_counts = c360_df["plan_name"].value_counts().reset_index()
            plan_counts.columns = ["Plan", "Subscribers"]
            fig_plan = px.bar(
                plan_counts, x="Plan", y="Subscribers",
                color="Plan",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_plan.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig_plan, use_container_width=True)
        else:
            st.info("No subscription data available.")

    with row1_c2:
        st.subheader("Customer Risk Tier Breakdown")
        if not pred_df.empty:
            risk_counts = pred_df["risk_tier"].value_counts().reset_index()
            risk_counts.columns = ["Risk Tier", "Count"]
            fig_pie = px.pie(
                risk_counts, names="Risk Tier", values="Count",
                color="Risk Tier",
                color_discrete_map={"LOW": "#22c55e", "MEDIUM": "#facc15", "HIGH": "#ef4444"},
                hole=0.55,
                template="plotly_dark"
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)


# -------------------------------------------------------------------------------------------------
# TAB 2: NETWORK OPERATIONS & INCIDENTS
# -------------------------------------------------------------------------------------------------
elif menu == "📡 Network Operations & NOC":
    st.title("Network Operations Center (NOC)")
    st.markdown("Cell tower telemetry, SLA violation monitoring, and automated incident triage.")

    if not net_df.empty:
        col1, col2 = st.columns([3, 2])
        with col1:
            st.subheader("Cell Tower Latency vs. Packet Loss")
            fig_scatter = px.scatter(
                net_df,
                x="avg_latency_ms",
                y="avg_packet_loss",
                size="peak_users",
                color="health_score",
                hover_data=["cell_id", "region", "technology", "avg_availability"],
                color_continuous_scale="RdYlGn",
                labels={"avg_latency_ms": "Average Latency (ms)", "avg_packet_loss": "Packet Loss (%)"},
                template="plotly_dark"
            )
            fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col2:
            st.subheader("Regional Performance Summary")
            reg_agg = net_df.groupby("region").agg(
                towers=("cell_id", "count"),
                avg_health=("health_score", "mean"),
                avg_latency=("avg_latency_ms", "mean")
            ).reset_index()
            st.dataframe(
                reg_agg.style.format({"avg_health": "{:.1f}", "avg_latency": "{:.1f} ms"}),
                use_container_width=True,
                hide_index=True
            )

        st.subheader("🚨 Automated Outage & Incident Alarms")
        if not inc_df.empty:
            st.dataframe(
                inc_df[["incident_id", "cell_id", "region", "severity", "latency_ms", "packet_loss_percentage", "availability_percentage", "affected_users_estimate", "status"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("All cell towers operating within normal SLA parameters. Zero active incidents.")


# -------------------------------------------------------------------------------------------------
# TAB 3: CUSTOMER 360 & CHURN
# -------------------------------------------------------------------------------------------------
elif menu == "👤 Customer 360 & Churn":
    st.title("Customer 360° Profile & Retention Intelligence")
    st.markdown("Consolidated customer lifecycle metrics, usage histories, and AI-driven churn prediction.")

    if not pred_df.empty:
        search_query = st.text_input("🔍 Search Customer by ID or Name", "")
        filtered_df = pred_df
        if search_query:
            filtered_df = pred_df[
                pred_df["customer_id"].str.contains(search_query, case=False, na=False) |
                pred_df.get("first_name", pd.Series()).str.contains(search_query, case=False, na=False) |
                pred_df.get("last_name", pd.Series()).str.contains(search_query, case=False, na=False)
            ]

        # Selected customer drilldown
        selected_cust_id = st.selectbox("Select Customer ID for Deep Dive", filtered_df["customer_id"].head(100).tolist())

        if selected_cust_id:
            cust_row = pred_df[pred_df["customer_id"] == selected_cust_id].iloc[0]
            c360_match = c360_df[c360_df["customer_id"] == selected_cust_id].iloc[0] if not c360_df.empty else None

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.markdown("### Profile")
                st.write(f"**Customer ID:** {cust_row['customer_id']}")
                if c360_match is not None and "first_name" in c360_match:
                    st.write(f"**Name:** {c360_match['first_name']} {c360_match['last_name']}")
                    st.write(f"**City:** {c360_match.get('city', 'N/A')}")
                    st.write(f"**Status:** {c360_match.get('customer_status', 'ACTIVE')}")

            with col2:
                st.markdown("### Subscription & Usage")
                st.write(f"**Plan:** {c360_match.get('plan_name', 'N/A') if c360_match is not None else 'N/A'}")
                st.write(f"**Contract:** {cust_row.get('contract_type', 'N/A')}")
                st.write(f"**Monthly Price:** ${cust_row.get('monthly_price', 0):.2f}")
                st.write(f"**Total Data Consumed:** {cust_row.get('total_data_gb', 0):.2f} GB")

            with col3:
                st.markdown("### Churn Risk Gauge")
                prob = float(cust_row["churn_probability"])
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=prob * 100,
                    title={'text': f"Risk: {cust_row['risk_tier']}"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#ef4444" if prob > 0.6 else ("#facc15" if prob > 0.25 else "#22c55e")},
                        'steps': [
                            {'range': [0, 25], 'color': "rgba(34, 197, 94, 0.2)"},
                            {'range': [25, 60], 'color': "rgba(250, 204, 21, 0.2)"},
                            {'range': [60, 100], 'color': "rgba(239, 68, 68, 0.2)"},
                        ],
                    }
                ))
                fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=220, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("---")
        st.subheader("Priority Retention Watchlist (Top High-Risk Subscribers)")
        st.dataframe(
            filtered_df[["customer_id", "churn_probability", "risk_tier", "contract_type", "monthly_price", "total_data_gb", "dropped_call_ratio", "failed_payments"]].head(25),
            use_container_width=True,
            hide_index=True
        )


# -------------------------------------------------------------------------------------------------
# TAB 4: ARCHITECTURE & MEDALLION PIPELINE
# -------------------------------------------------------------------------------------------------
elif menu == "🏗️ Architecture & Pipeline":
    st.title("Medallion Lakehouse Architecture")
    st.markdown("""
    The **Telecom 360°** platform is structured around a three-tier Medallion architecture designed for high scalability, ACID consistency, and historical accuracy.
    """)

    st.markdown("""
    ```
    ┌──────────────────────┐
    │  Raw Ingestion       │ Customers, Subscriptions, Billing, CDRs, Telemetry, Usage
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  🥉 Bronze Layer     │ Raw schema preservation, ingestion timestamping, append-only
    └──────────┬───────────┘
               │
               ├────────────────────────────┐
               ▼                            ▼
    ┌──────────────────────┐     ┌──────────────────────┐
    │  🥈 Silver Layer     │     │  🚫 Quarantine Zone  │ Schema breaches, negative duration,
    │  Deduplication, SCD2 │     │  Invalid Records     │ out-of-bounds latency
    └──────────┬───────────┘     └──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  🥇 Gold Layer       │ Customer 360, Network Health, SLA Alarms, ARPU Summary
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  🤖 Machine Learning │ XGBoost Churn Classification & Prioritized Watchlist
    └──────────────────────┘
    ```
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Pipeline Components")
        st.markdown("""
        - **Streaming Engine**: Kafka topics `telecom.cdr`, `telecom.network`, `telecom.usage`
        - **Data Quality Framework**: Non-null checks, range validation, automated quarantine routing
        - **Dimensional Modeling**: SCD Type 2 tracking for subscription plan transitions
        """)
    with col2:
        st.subheader("Analytics & Serving")
        st.markdown("""
        - **Storage Format**: Apache Parquet & Delta Lake
        - **ML Framework**: XGBoost Churn Classification with Scikit-learn feature pipeline
        - **Query Layer**: DuckDB & Snowflake-compatible SQL marts
        """)
