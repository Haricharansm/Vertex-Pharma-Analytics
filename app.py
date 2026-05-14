"""
app.py — Vertex Pharma Predictive Analytics Prototype
Streamlit application with three tabs:
  1. Demand Forecast
  2. Inventory Optimizer
  3. What-If Simulation
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from data import DEFAULT_PARAMS
from models import (
    run_forecast,
    run_inventory,
    run_whatif,
    build_tradeoff_curve,
    get_reorder_table,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vertex Pharma · Predictive Analytics",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        padding: 0 20px;
        font-size: 14px;
        font-weight: 500;
    }
    div[data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px 16px;
    }
    .insight-box {
        background: #f0f4ff;
        border-left: 4px solid #534AB7;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        font-size: 14px;
        line-height: 1.6;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_title:
    st.markdown("## 💊 Vertex Pharma · AI Predictive Analytics")
    st.caption(
        "Demand forecasting · Inventory optimization · What-if scenario simulation"
    )

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📈  Demand Forecast",
    "📦  Inventory Optimizer",
    "🔬  What-If Simulation",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DEMAND FORECAST
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Demand Forecast — Trikafta (ivacaftor/tezacaftor/elexacaftor)")
    st.caption("Adjust leading indicators below to see the AI model re-project demand in real time.")

    # Controls
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        payer = st.slider(
            "Payer coverage expansion (%)",
            min_value=0, max_value=30,
            value=DEFAULT_PARAMS["payer_coverage"],
            help="Increase in commercial and government formulary coverage vs baseline"
        )
    with ctrl2:
        awareness = st.slider(
            "Physician awareness index",
            min_value=50, max_value=100,
            value=DEFAULT_PARAMS["physician_awareness"],
            help="Composite index of HCP detailing reach and message recall (50–100)"
        )
    with ctrl3:
        diag_rate = st.slider(
            "New diagnosis rate (monthly)",
            min_value=100, max_value=400,
            value=DEFAULT_PARAMS["diag_rate"],
            help="Estimated new CF patients diagnosed per month nationally"
        )

    result = run_forecast(payer, awareness, diag_rate)

    # KPIs
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Predicted Q3 scripts", f"{result['q3_scripts']:,}", "+12% vs Q2")
    m2.metric("Forecast accuracy", "94.1%", "+2.3pp YoY")
    m3.metric("New patient starts", f"{result['nps']:,}", "+8% vs prior")
    m4.metric("Confidence interval", "±4.2%", "95% CI", delta_color="off")

    st.markdown("")

    # Chart
    df = result["df"]
    fig = go.Figure()

    # CI band
    ci_months = [m for m, v in zip(df["Month"], df["Upper CI (95%)"]) if v is not None]
    ci_upper = [v for v in df["Upper CI (95%)"] if v is not None]
    ci_lower = [v for v in df["Lower CI (95%)"] if v is not None]

    fig.add_trace(go.Scatter(
        x=ci_months + ci_months[::-1],
        y=ci_upper + ci_lower[::-1],
        fill="toself",
        fillcolor="rgba(29,158,117,0.10)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        name="95% CI",
        showlegend=True,
    ))

    # Actual
    fig.add_trace(go.Scatter(
        x=df["Month"],
        y=df["Actual"],
        mode="lines+markers",
        name="Actual",
        line=dict(color="#534AB7", width=2.5),
        marker=dict(size=6),
        connectgaps=False,
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=df["Month"],
        y=df["Forecast"],
        mode="lines+markers",
        name="AI Forecast",
        line=dict(color="#1D9E75", width=2.5, dash="dash"),
        marker=dict(size=5),
        connectgaps=False,
    ))

    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            tickformat=",",
            ticksuffix=" ",
            gridcolor="rgba(0,0,0,0.06)",
            title="Scripts",
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Insight
    st.markdown(
        f"<div class='insight-box'>💡 <strong>AI insight:</strong> {result['insight']}</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INVENTORY OPTIMIZER
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Inventory Optimizer — Safety Stock & Reorder Intelligence")
    st.caption("AI re-optimizes safety stock continuously as demand signals and supply variability shift.")

    left, right = st.columns([1, 1])

    with left:
        svc_level = st.slider(
            "Service level target (%)",
            min_value=90, max_value=99,
            value=DEFAULT_PARAMS["service_level"],
            help="Target probability of no stockout during replenishment cycle"
        )
        lead_time_var = st.slider(
            "Lead time variability (σ, days)",
            min_value=1, max_value=14,
            value=DEFAULT_PARAMS["lead_time_var"],
            help="Standard deviation of supplier lead time"
        )
        demand_cv = st.slider(
            "Demand variability (CV × 100)",
            min_value=5, max_value=40,
            value=DEFAULT_PARAMS["demand_cv"],
            help="Coefficient of variation of daily demand × 100"
        )

        inv_result = run_inventory(svc_level, lead_time_var, demand_cv)

        im1, im2 = st.columns(2)
        im1.metric("Safety stock (days)", inv_result["ss_days"], "AI-optimized")
        savings = inv_result["savings"]
        im2.metric(
            "Carrying cost impact",
            f"{'+'if savings < 0 else '-'}${abs(savings)/1e6:.1f}M",
            "vs static model",
            delta_color="inverse",
        )
        im3, im4 = st.columns(2)
        im3.metric("Stockout risk", f"{inv_result['stockout_risk']}%")
        im4.metric("Service level", f"{svc_level}%")

        st.markdown(
            f"<div class='insight-box'>💡 <strong>AI recommendation:</strong> {inv_result['insight']}</div>",
            unsafe_allow_html=True,
        )

    with right:
        # Tradeoff curve
        curve_df = build_tradeoff_curve()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=curve_df.index,
            y=curve_df["Safety Stock (days)"],
            mode="lines+markers",
            line=dict(color="#534AB7", width=2.5),
            marker=dict(size=6),
            fill="toself",
            fillcolor="rgba(83,74,183,0.08)",
            name="Safety stock",
        ))
        # Highlight current selection
        current_ss = inv_result["ss_days"]
        fig2.add_trace(go.Scatter(
            x=[svc_level],
            y=[current_ss],
            mode="markers",
            marker=dict(color="#D85A30", size=12, symbol="circle"),
            name=f"Current ({svc_level}% → {current_ss}d)",
        ))
        fig2.update_layout(
            title="Service level vs. safety stock tradeoff",
            height=270,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(title="Service level (%)", showgrid=False),
            yaxis=dict(title="Safety stock (days)", gridcolor="rgba(0,0,0,0.06)"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Reorder table
    st.markdown("#### SKU-level reorder recommendations")
    reorder_df = get_reorder_table(svc_level, lead_time_var)
    st.dataframe(
        reorder_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Product": st.column_config.TextColumn("Product", width="large"),
            "SKU": st.column_config.TextColumn("SKU", width="small"),
            "Stock (units)": st.column_config.TextColumn("Stock (units)"),
            "Days on hand": st.column_config.NumberColumn("Days on hand", format="%d days"),
            "Status": st.column_config.TextColumn("Status"),
            "Recommended order": st.column_config.TextColumn("Recommended order"),
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — WHAT-IF SIMULATION
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### What-If Simulation — Monte Carlo Scenario Engine")
    st.caption("10,000 simulation runs per configuration. Adjust levers to see the probability distribution of outcomes.")

    sc1, sc2 = st.columns([1, 2])

    with sc1:
        comp_prob = st.slider(
            "Competitor FDA approval probability (%)",
            min_value=0, max_value=100,
            value=DEFAULT_PARAMS["competitor_prob"],
            help="Estimated probability a key competitor receives FDA approval in the next 18 months"
        )
        new_markets = st.slider(
            "New market expansion (geographies)",
            min_value=0, max_value=10,
            value=DEFAULT_PARAMS["new_markets"],
            help="Number of new international or regional markets entering"
        )
        psp_uplift = st.slider(
            "Patient support program uplift (%)",
            min_value=0, max_value=50,
            value=DEFAULT_PARAMS["psp_uplift"],
            help="Expected increase in patient adherence and starts from PSP investment"
        )
        price_elast = st.slider(
            "Price sensitivity (% elasticity)",
            min_value=0, max_value=30,
            value=DEFAULT_PARAMS["price_elasticity"],
            help="Demand reduction per 1% price increase"
        )

    wi = run_whatif(comp_prob, new_markets, psp_uplift, price_elast)

    with sc2:
        wm1, wm2, wm3, wm4 = st.columns(4)
        rev_delta_color = "normal" if wi["rev_impact"] >= 0 else "inverse"
        wm1.metric(
            "Projected revenue impact",
            wi["rev_label"],
            "vs base case",
            delta_color=rev_delta_color,
        )
        wm2.metric("Script volume change", wi["script_change"], "net of competition")
        risk_color = {"Low": "normal", "Medium": "off", "High": "inverse"}
        wm3.metric("Supply chain risk", wi["risk_level"], wi["risk_sub"])
        wm4.metric("Model confidence", f"{wi['confidence']}%", "10k sim runs", delta_color="off")

        # Scenario chart
        sdf = wi["scenario_df"].reset_index()
        fig3 = go.Figure()

        line_styles = {
            "Base case": dict(color="#888780", dash="dash", width=2),
            "Optimistic": dict(color="#1D9E75", dash="solid", width=2.5),
            "Pessimistic": dict(color="#D85A30", dash="solid", width=2.5),
        }
        for col in ["Base case", "Optimistic", "Pessimistic"]:
            fig3.add_trace(go.Scatter(
                x=sdf["Quarter"],
                y=sdf[col],
                mode="lines+markers",
                name=col,
                line=line_styles[col],
                marker=dict(size=6),
            ))

        fig3.update_layout(
            height=280,
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(
                title="Script volume ('000s)",
                gridcolor="rgba(0,0,0,0.06)",
                ticksuffix="k",
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            hovermode="x unified",
        )
        st.plotly_chart(fig3, use_container_width=True)

    # P10/P90 range bar
    st.markdown("#### Revenue distribution (P10 → P90 range)")
    range_df = pd.DataFrame({
        "Scenario": ["Pessimistic (P10)", "Expected", "Optimistic (P90)"],
        "Revenue Impact ($M)": [round(wi["p10"]), round(wi["rev_impact"]), round(wi["p90"])],
    })
    fig4 = px.bar(
        range_df,
        x="Revenue Impact ($M)",
        y="Scenario",
        orientation="h",
        color="Revenue Impact ($M)",
        color_continuous_scale=["#D85A30", "#534AB7", "#1D9E75"],
        text="Revenue Impact ($M)",
    )
    fig4.update_traces(texttemplate="%{text:+.0f}M", textposition="outside")
    fig4.update_layout(
        height=200,
        margin=dict(l=0, r=60, t=10, b=0),
        showlegend=False,
        coloraxis_showscale=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="rgba(0,0,0,0.2)"),
        yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig4, use_container_width=True)

    # Insight
    st.markdown(
        f"<div class='insight-box'>💡 <strong>AI simulation summary:</strong> {wi['insight']}</div>",
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Prototype · Vertex Pharma Predictive Analytics · "
    "All figures are illustrative model outputs, not actual Vertex data."
)
