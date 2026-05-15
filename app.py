"""
app.py — Vertex Pharma Predictive Analytics Prototype
Streamlit app — Vertex brand + enhanced UX
Tabs:
  0. Executive Summary  (NEW)
  1. Demand Forecast    (enhanced: waterfall driver chart)
  2. Inventory Optimizer(enhanced: carrying cost bar, progress columns)
  3. What-If Simulation (enhanced: risk gauge, tornado chart)
  4. AI Insights Chat   (NEW)
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

from data import DEFAULT_PARAMS, PRODUCTS
from models import (
    run_forecast,
    run_inventory,
    run_whatif,
    build_tradeoff_curve,
    get_reorder_table,
)

# ── Brand tokens ──────────────────────────────────────────────────────────────
VTX_PURPLE       = "#4B2D8F"
VTX_PURPLE_DARK  = "#3D1F7A"
VTX_PURPLE_LITE  = "#EEE9F8"
VTX_CORAL        = "#E8734A"
VTX_CORAL_LITE   = "#FDF0EB"
VTX_TEAL         = "#1D9E75"
VTX_RED          = "#C0392B"
VTX_GREY         = "#6B7280"
VTX_BG           = "#F9F8FC"
CHART_FONT       = dict(family="Inter, Helvetica Neue, sans-serif", size=12, color="#374151")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vertex Pharma · AI Analytics",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: {VTX_BG}; }}
.main .block-container {{ padding: 0 2rem 2rem 2rem; max-width: 1400px; }}

/* Header */
.vtx-header {{
    background: linear-gradient(135deg, {VTX_PURPLE_DARK} 0%, {VTX_PURPLE} 60%, #6B4DB5 100%);
    padding: 1.4rem 2rem;
    border-radius: 0 0 16px 16px;
    display: flex; align-items: center; gap: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(75,45,143,0.25);
}}
.vtx-logo-mark {{
    width: 40px; height: 40px; background: white; flex-shrink: 0;
    clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
}}
.vtx-title {{ color: white; }}
.vtx-title h1 {{ font-size: 1.3rem; font-weight: 700; margin: 0; letter-spacing: -0.3px; }}
.vtx-title p  {{ font-size: 0.78rem; margin: 3px 0 0; opacity: 0.78; font-weight: 300; }}
.vtx-badge {{
    margin-left: auto;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px; padding: 4px 14px;
    color: white; font-size: 12px; font-weight: 500; white-space: nowrap;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px; background: white; border-radius: 12px;
    padding: 6px; border: 1px solid #E5E7EB; margin-bottom: 1.5rem;
}}
.stTabs [data-baseweb="tab"] {{
    height: 36px; padding: 0 18px; font-size: 13px;
    font-weight: 500; border-radius: 8px; color: {VTX_GREY};
}}
.stTabs [aria-selected="true"] {{
    background: {VTX_PURPLE} !important; color: white !important;
}}

/* Metrics */
div[data-testid="metric-container"] {{
    background: white; border: 1px solid #E5E7EB;
    border-radius: 12px; padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}}
div[data-testid="metric-container"] > div:first-child {{
    font-size: 11px !important; color: {VTX_GREY} !important;
    font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 1.55rem !important; font-weight: 700 !important; color: {VTX_PURPLE_DARK} !important;
}}

/* Section header */
.section-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }}
.section-icon {{
    width: 32px; height: 32px; background: {VTX_PURPLE_LITE};
    border-radius: 8px; display: flex; align-items: center;
    justify-content: center; font-size: 15px; flex-shrink: 0;
}}
.section-title {{ font-size: 1rem; font-weight: 600; color: {VTX_PURPLE_DARK}; margin: 0; }}
.section-sub   {{ font-size: 12px; color: {VTX_GREY}; margin: 0; }}

/* Callout boxes */
.insight-box {{
    background: {VTX_PURPLE_LITE}; border-left: 4px solid {VTX_PURPLE};
    padding: 14px 18px; border-radius: 0 10px 10px 0;
    font-size: 13.5px; line-height: 1.7; margin-top: 1rem; color: #1F1535;
}}
.insight-box b {{ color: {VTX_PURPLE_DARK}; }}
.alert-box {{
    background: #FEF3C7; border-left: 4px solid #F59E0B;
    padding: 12px 18px; border-radius: 0 10px 10px 0;
    font-size: 13px; line-height: 1.6; margin-top: 0.5rem;
}}
.success-box {{
    background: #ECFDF5; border-left: 4px solid {VTX_TEAL};
    padding: 12px 18px; border-radius: 0 10px 10px 0;
    font-size: 13px; line-height: 1.6; margin-top: 0.5rem;
}}

/* Exec cards */
.exec-card {{
    background: white; border-radius: 14px; padding: 1.25rem 1.5rem;
    border: 1px solid #E5E7EB; box-shadow: 0 2px 8px rgba(75,45,143,0.07); height: 100%;
}}
.exec-card-title {{
    font-size: 11px; font-weight: 600; color: {VTX_GREY};
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.4rem;
}}
.exec-card-value {{ font-size: 1.9rem; font-weight: 700; color: {VTX_PURPLE_DARK}; line-height: 1.1; }}
.exec-card-sub   {{ font-size: 12.5px; margin-top: 4px; }}
.trend-up   {{ color: {VTX_TEAL}; font-weight: 600; }}
.trend-warn {{ color: #D97706; font-weight: 600; }}
.trend-neutral {{ color: {VTX_GREY}; }}

/* Chat */
.chat-msg-user {{
    background: {VTX_PURPLE}; color: white;
    padding: 10px 16px; border-radius: 16px 16px 4px 16px;
    margin: 6px 0 6px 15%; font-size: 13.5px; line-height: 1.6;
}}
.chat-msg-ai {{
    background: white; border: 1px solid #E5E7EB;
    padding: 12px 16px; border-radius: 4px 16px 16px 16px;
    margin: 6px 15% 6px 0; font-size: 13.5px; line-height: 1.7; color: #1F1535;
}}

/* Sliders */
.stSlider > div > div > div > div {{ background: {VTX_PURPLE} !important; }}

/* Primary button */
.stButton > button[kind="primary"] {{
    background: {VTX_PURPLE} !important; border: none !important; color: white !important;
    border-radius: 8px !important; font-weight: 500 !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: {VTX_PURPLE_DARK} !important;
}}

/* Footer */
.vtx-footer {{
    text-align: center; padding: 1.2rem; font-size: 11px;
    color: #9CA3AF; margin-top: 1.5rem; border-top: 1px solid #E5E7EB;
}}

hr {{ border-color: #E5E7EB; }}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="vtx-header">
    <div class="vtx-logo-mark"></div>
    <div class="vtx-title">
        <h1>VERTEX &nbsp;|&nbsp; AI Predictive Analytics</h1>
        <p>Demand Intelligence &nbsp;·&nbsp; Inventory Optimization &nbsp;·&nbsp; Scenario Simulation</p>
    </div>
    <div class="vtx-badge">🟢 Live Prototype &nbsp;·&nbsp; {datetime.now().strftime('%B %d, %Y')}</div>
</div>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def base_layout(height=320, title=None):
    layout = dict(
        height=height,
        margin=dict(l=0, r=10, t=36 if title else 16, b=0),
        plot_bgcolor="white", paper_bgcolor="white",
        font=CHART_FONT, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, font=dict(size=11)),
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=11)),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(size=13, color=VTX_PURPLE_DARK))
    return layout

def section(icon, title, sub=""):
    sub_html = f"<p class='section-sub'>{sub}</p>" if sub else ""
    st.markdown(f"""
    <div class="section-header">
      <div class="section-icon">{icon}</div>
      <div><p class="section-title">{title}</p>{sub_html}</div>
    </div>""", unsafe_allow_html=True)

def callout(text, kind="insight"):
    css = {"insight": "insight-box", "alert": "alert-box", "success": "success-box"}
    st.markdown(f"<div class='{css.get(kind, 'insight-box')}'>{text}</div>",
                unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "🏠  Executive Summary",
    "📈  Demand Forecast",
    "📦  Inventory Optimizer",
    "🔬  What-If Simulation",
    "💬  AI Insights Chat",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
with tab0:
    section("🏠", "Executive Summary",
            "AI-driven commercial and supply chain intelligence at a glance")

    # KPI cards
    e1, e2, e3, e4, e5 = st.columns(5)
    kpis = [
        ("Q3 Script Forecast",   "48,200", "↑ 12% vs Q2",           "trend-up"),
        ("Forecast Accuracy",    "94.1%",  "↑ 2.3pp YoY",           "trend-up"),
        ("Inventory Savings",    "$3.1M",  "vs static model",        "trend-up"),
        ("SKUs Needing Action",  "1 of 4", "Symdeko below minimum",  "trend-warn"),
        ("Scenario Confidence",  "81%",    "10k Monte Carlo runs",   "trend-neutral"),
    ]
    for col, (lbl, val, sub, cls) in zip([e1, e2, e3, e4, e5], kpis):
        col.markdown(f"""
        <div class="exec-card">
          <div class="exec-card-title">{lbl}</div>
          <div class="exec-card-value">{val}</div>
          <div class="exec-card-sub {cls}">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left_col, right_col = st.columns([3, 2])

    with left_col:
        section("📈", "12-Month Demand Trajectory — Trikafta")
        exec_fc = run_forecast(15, 72, 230)
        df_e = exec_fc["df"]
        fig_e = go.Figure()
        ci_m = [m for m, v in zip(df_e["Month"], df_e["Upper CI (95%)"]) if v]
        u_vals = [v for v in df_e["Upper CI (95%)"] if v]
        l_vals = [v for v in df_e["Lower CI (95%)"] if v]
        fig_e.add_trace(go.Scatter(
            x=ci_m + ci_m[::-1], y=u_vals + l_vals[::-1],
            fill="toself", fillcolor="rgba(75,45,143,0.09)",
            line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", name="95% CI",
        ))
        fig_e.add_trace(go.Scatter(
            x=df_e["Month"], y=df_e["Actual"], mode="lines+markers",
            name="Actual", line=dict(color=VTX_PURPLE, width=2.5),
            marker=dict(size=7, color=VTX_PURPLE),
        ))
        fig_e.add_trace(go.Scatter(
            x=df_e["Month"], y=df_e["Forecast"], mode="lines+markers",
            name="AI Forecast", line=dict(color=VTX_CORAL, width=2.5, dash="dash"),
            marker=dict(size=6, color=VTX_CORAL),
        ))
        fig_e.update_layout(**base_layout(280))
        fig_e.update_yaxes(title="Scripts", tickformat=",")
        st.plotly_chart(fig_e, use_container_width=True)

    with right_col:
        section("⚠️", "Alerts & Recommendations")
        callout("<b>🔴 Symdeko below minimum stock</b><br>Order 8,200 units immediately — "
                "12 days on hand vs 15-day minimum.", "alert")
        callout("<b>🟡 Trikafta at reorder threshold</b><br>Initiate PO for 14,000 units "
                "to maintain 96% service level.", "alert")
        callout("<b>🟢 Q3 demand tracking above plan</b><br>Payer expansion driving "
                "+12% vs prior quarter.", "success")
        callout("<b>🔵 Scenario outlook: +$124M</b><br>Base case with 30% competitor "
                "probability and 2 new markets.", "insight")

    st.markdown("<br>", unsafe_allow_html=True)
    section("📦", "Portfolio Health Overview")
    portfolio_df = pd.DataFrame({
        "Product":               ["Trikafta", "Kalydeco", "Symdeko", "Orkambi"],
        "Days on Hand":          [16, 131, 12, 76],
        "Status":                ["🟡 At threshold", "🟢 Healthy", "🔴 Below min", "🟢 Healthy"],
        "Q3 Demand Trend":       ["↑ Strong", "→ Stable", "↑ Recovering", "→ Stable"],
        "Forecast Accuracy (%)": [94, 91, 88, 92],
        "Revenue Mix":           ["68%", "14%", "11%", "7%"],
    })
    st.dataframe(
        portfolio_df, use_container_width=True, hide_index=True,
        column_config={
            "Days on Hand": st.column_config.ProgressColumn(
                "Days on Hand", min_value=0, max_value=150, format="%d days"),
            "Forecast Accuracy (%)": st.column_config.ProgressColumn(
                "Forecast Accuracy", min_value=0, max_value=100, format="%d%%"),
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DEMAND FORECAST
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    section("📈", "Demand Forecast — Trikafta (ivacaftor/tezacaftor/elexacaftor)",
            "Adjust leading indicators to re-project demand in real time")

    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        payer = st.slider("Payer coverage expansion (%)", 0, 30,
                          DEFAULT_PARAMS["payer_coverage"],
                          help="Increase in commercial and government formulary coverage vs baseline")
    with ctrl2:
        awareness = st.slider("Physician awareness index", 50, 100,
                              DEFAULT_PARAMS["physician_awareness"],
                              help="Composite index of HCP detailing reach and message recall (50–100)")
    with ctrl3:
        diag_rate = st.slider("New diagnosis rate (monthly)", 100, 400,
                              DEFAULT_PARAMS["diag_rate"],
                              help="Estimated new CF patients diagnosed per month nationally")

    result = run_forecast(payer, awareness, diag_rate)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Predicted Q3 Scripts", f"{result['q3_scripts']:,}", "+12% vs Q2")
    m2.metric("Forecast Accuracy",    "94.1%",                    "+2.3pp YoY")
    m3.metric("New Patient Starts",   f"{result['nps']:,}",       "+8% vs prior")
    m4.metric("Confidence Interval",  "±4.2%",                    "95% CI", delta_color="off")
    st.markdown("")

    # Main forecast chart
    df = result["df"]
    fig = go.Figure()
    ci_months = [m for m, v in zip(df["Month"], df["Upper CI (95%)"]) if v]
    fig.add_trace(go.Scatter(
        x=ci_months + ci_months[::-1],
        y=[v for v in df["Upper CI (95%)"] if v] + [v for v in df["Lower CI (95%)"] if v][::-1],
        fill="toself", fillcolor="rgba(75,45,143,0.09)",
        line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", name="95% CI",
    ))
    fig.add_trace(go.Scatter(
        x=df["Month"], y=df["Actual"], mode="lines+markers", name="Actual",
        line=dict(color=VTX_PURPLE, width=2.5), marker=dict(size=7, color=VTX_PURPLE),
    ))
    fig.add_trace(go.Scatter(
        x=df["Month"], y=df["Forecast"], mode="lines+markers", name="AI Forecast",
        line=dict(color=VTX_CORAL, width=2.5, dash="dash"),
        marker=dict(size=6, color=VTX_CORAL),
    ))
    fig.update_layout(**base_layout(330))
    fig.update_yaxes(title="Scripts", tickformat=",")
    st.plotly_chart(fig, use_container_width=True)

    # Waterfall: driver decomposition
    section("🔍", "Forecast Driver Decomposition",
            "Contribution of each leading indicator to the forecast vs. baseline")
    base_val    = 44100
    payer_cont  = round((payer - 15) * 0.004 * base_val)
    aware_cont  = round((awareness - 72) * 0.003 * base_val)
    diag_cont   = round((diag_rate - 230) * 0.0015 * base_val)
    final_val   = base_val + payer_cont + aware_cont + diag_cont
    drivers     = ["Baseline", "Payer coverage", "Physician awareness", "Diagnosis rate", "Forecast"]
    values      = [base_val, payer_cont, aware_cont, diag_cont, final_val]
    measures    = ["absolute", "relative", "relative", "relative", "total"]
    texts       = [f"{base_val:,}", f"{payer_cont:+,}", f"{aware_cont:+,}",
                   f"{diag_cont:+,}", f"{final_val:,}"]
    fig_wf = go.Figure(go.Waterfall(
        x=drivers, measure=measures, y=values,
        connector=dict(line=dict(color="#E5E7EB", width=1.5)),
        decreasing=dict(marker_color=VTX_RED),
        increasing=dict(marker_color=VTX_TEAL),
        totals=dict(marker_color=VTX_CORAL),
        text=texts, textposition="outside",
        textfont=dict(size=11),
    ))
    fig_wf.update_layout(**base_layout(260))
    fig_wf.update_yaxes(title="Scripts", tickformat=",")
    st.plotly_chart(fig_wf, use_container_width=True)

    callout(f"💡 <b>AI Insight:</b> {result['insight']}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INVENTORY OPTIMIZER
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    section("📦", "Inventory Optimizer — Safety Stock & Reorder Intelligence",
            "AI re-optimizes safety stock continuously as demand and supply variability shift")

    left, right = st.columns([1, 1])

    with left:
        svc_level     = st.slider("Service level target (%)", 90, 99,
                                  DEFAULT_PARAMS["service_level"],
                                  help="Target probability of no stockout during replenishment cycle")
        lead_time_var = st.slider("Lead time variability (σ, days)", 1, 14,
                                  DEFAULT_PARAMS["lead_time_var"],
                                  help="Standard deviation of CMO / supplier lead time")
        demand_cv     = st.slider("Demand variability (CV × 100)", 5, 40,
                                  DEFAULT_PARAMS["demand_cv"],
                                  help="Coefficient of variation of daily demand × 100")

        inv_result = run_inventory(svc_level, lead_time_var, demand_cv)
        savings    = inv_result["savings"]

        im1, im2 = st.columns(2)
        im1.metric("Safety Stock (days)", inv_result["ss_days"], "AI-optimized")
        im2.metric("Carrying Cost Impact",
                   f"{'+'if savings<0 else '-'}${abs(savings)/1e6:.1f}M",
                   "vs static model", delta_color="inverse")
        im3, im4 = st.columns(2)
        im3.metric("Stockout Risk",  f"{inv_result['stockout_risk']}%")
        im4.metric("Service Level",  f"{svc_level}%")

        callout(f"💡 <b>AI Recommendation:</b> {inv_result['insight']}")

    with right:
        # Tradeoff curve
        curve_df = build_tradeoff_curve()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=curve_df.index, y=curve_df["Safety Stock (days)"],
            mode="lines+markers",
            line=dict(color=VTX_PURPLE, width=2.5),
            marker=dict(size=6, color=VTX_PURPLE),
            fill="tozeroy", fillcolor="rgba(75,45,143,0.07)",
            name="Safety stock curve",
        ))
        fig2.add_trace(go.Scatter(
            x=[svc_level], y=[inv_result["ss_days"]],
            mode="markers",
            marker=dict(color=VTX_CORAL, size=14, symbol="circle",
                        line=dict(color="white", width=2)),
            name=f"Selected ({svc_level}% → {inv_result['ss_days']}d)",
        ))
        fig2.update_layout(**base_layout(260, "Service level vs. safety stock tradeoff"))
        fig2.update_xaxes(title="Service level (%)")
        fig2.update_yaxes(title="Safety stock (days)")
        st.plotly_chart(fig2, use_container_width=True)

        # Carrying cost bar chart
        svc_range  = list(range(90, 100))
        cost_vals  = [(curve_df.loc[s, "Safety Stock (days)"] - 42) * -170 for s in svc_range]
        fig_cc = go.Figure(go.Bar(
            x=svc_range, y=cost_vals,
            marker_color=[VTX_CORAL if s == svc_level else VTX_PURPLE for s in svc_range],
            text=[f"${v:.0f}K" for v in cost_vals],
            textposition="outside", textfont=dict(size=10),
        ))
        fig_cc.update_layout(**base_layout(210, "Carrying cost savings vs. static model ($K)"))
        fig_cc.update_xaxes(title="Service level (%)", tickvals=svc_range)
        fig_cc.update_yaxes(title="Savings ($K)")
        st.plotly_chart(fig_cc, use_container_width=True)

    st.markdown("---")
    section("🗂️", "SKU-Level Reorder Recommendations")
    reorder_df = get_reorder_table(svc_level, lead_time_var)
    st.dataframe(
        reorder_df, use_container_width=True, hide_index=True,
        column_config={
            "Product":           st.column_config.TextColumn("Product", width="large"),
            "SKU":               st.column_config.TextColumn("SKU", width="small"),
            "Stock (units)":     st.column_config.TextColumn("Current Stock"),
            "Days on hand":      st.column_config.ProgressColumn(
                                    "Days on Hand", min_value=0, max_value=150, format="%d days"),
            "Status":            st.column_config.TextColumn("Status"),
            "Recommended order": st.column_config.TextColumn("Recommended Order"),
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — WHAT-IF SIMULATION
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    section("🔬", "What-If Simulation — Monte Carlo Scenario Engine",
            "10,000 simulation runs per configuration · adjust levers to explore outcome distributions")

    sc1, sc2 = st.columns([1, 2])

    with sc1:
        comp_prob   = st.slider("Competitor FDA approval probability (%)", 0, 100,
                                DEFAULT_PARAMS["competitor_prob"],
                                help="Estimated probability a key competitor receives FDA approval in the next 18 months")
        new_markets = st.slider("New market expansion (geographies)", 0, 10,
                                DEFAULT_PARAMS["new_markets"],
                                help="Number of new international or regional markets entering")
        psp_uplift  = st.slider("Patient support program uplift (%)", 0, 50,
                                DEFAULT_PARAMS["psp_uplift"],
                                help="Expected increase in patient adherence and starts from PSP investment")
        price_elast = st.slider("Price sensitivity (% elasticity)", 0, 30,
                                DEFAULT_PARAMS["price_elasticity"],
                                help="Demand reduction per 1% price increase")

        # Risk gauge
        risk_score = min(100, max(0,
            comp_prob * 0.6 + price_elast * 1.2 - new_markets * 3 - psp_uplift * 0.5))
        risk_color = VTX_RED if risk_score > 60 else ("#F59E0B" if risk_score > 35 else VTX_TEAL)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title=dict(text="Composite Risk Score", font=dict(size=12, color=VTX_PURPLE_DARK)),
            gauge=dict(
                axis=dict(range=[0, 100], tickfont=dict(size=10)),
                bar=dict(color=risk_color, thickness=0.3),
                bgcolor="white",
                steps=[
                    dict(range=[0,  35], color="#ECFDF5"),
                    dict(range=[35, 65], color="#FEF3C7"),
                    dict(range=[65,100], color="#FEF2F2"),
                ],
                threshold=dict(line=dict(color=VTX_PURPLE_DARK, width=2.5),
                               thickness=0.75, value=risk_score),
            ),
            number=dict(suffix="/100", font=dict(color=risk_color, size=26)),
        ))
        fig_gauge.update_layout(
            height=210, margin=dict(l=10, r=10, t=40, b=0), paper_bgcolor="white")
        st.plotly_chart(fig_gauge, use_container_width=True)

    wi = run_whatif(comp_prob, new_markets, psp_uplift, price_elast)

    with sc2:
        wm1, wm2, wm3, wm4 = st.columns(4)
        wm1.metric("Revenue Impact",    wi["rev_label"],          "vs base case")
        wm2.metric("Script Volume",     wi["script_change"],      "net of competition")
        wm3.metric("Supply Chain Risk", wi["risk_level"],         wi["risk_sub"])
        wm4.metric("Model Confidence",  f"{wi['confidence']}%",   "10k sim runs", delta_color="off")

        sdf = wi["scenario_df"].reset_index()
        fig3 = go.Figure()
        for col_name, style, fill_c in [
            ("Base case",   dict(color=VTX_GREY,  dash="dot",   width=2),   None),
            ("Optimistic",  dict(color=VTX_TEAL,  dash="solid", width=2.5), "rgba(29,158,117,0.08)"),
            ("Pessimistic", dict(color=VTX_RED,   dash="solid", width=2.5), "rgba(192,57,43,0.08)"),
        ]:
            fig3.add_trace(go.Scatter(
                x=sdf["Quarter"], y=sdf[col_name],
                mode="lines+markers", name=col_name,
                line=style, marker=dict(size=7),
                fill="tozeroy" if fill_c else None,
                fillcolor=fill_c,
            ))
        fig3.update_layout(**base_layout(265))
        fig3.update_yaxes(title="Script volume ('000s)", ticksuffix="k")
        st.plotly_chart(fig3, use_container_width=True)

    # Tornado chart
    st.markdown("---")
    section("🌪️", "Sensitivity Tornado",
            "Revenue impact of each lever relative to baseline — largest drivers at top")
    levers  = ["Market expansion", "PSP uplift", "Competitor approval", "Price elasticity"]
    impacts = [new_markets*18, psp_uplift*3.4, -comp_prob*2.1, -price_elast*1.2]
    sorted_data = sorted(zip(np.abs(impacts), levers, impacts), reverse=True)
    _, levers_s, impacts_s = zip(*sorted_data)
    colors_s = [VTX_TEAL if v >= 0 else VTX_RED for v in impacts_s]
    fig_t = go.Figure(go.Bar(
        x=list(impacts_s), y=list(levers_s), orientation="h",
        marker_color=colors_s,
        text=[f"{v:+.0f}M" for v in impacts_s],
        textposition="outside", textfont=dict(size=11),
    ))
    fig_t.update_layout(**base_layout(220))
    fig_t.update_xaxes(title="Revenue impact ($M)", zeroline=True,
                       zerolinecolor="#374151", zerolinewidth=1.5)
    fig_t.update_yaxes(showgrid=False)
    st.plotly_chart(fig_t, use_container_width=True)

    # P10/Expected/P90 bar
    range_df = pd.DataFrame({
        "Scenario":             ["Pessimistic (P10)", "Expected", "Optimistic (P90)"],
        "Revenue Impact ($M)":  [round(wi["p10"]), round(wi["rev_impact"]), round(wi["p90"])],
    })
    fig4 = px.bar(
        range_df, x="Revenue Impact ($M)", y="Scenario", orientation="h",
        color="Revenue Impact ($M)",
        color_continuous_scale=[[0, VTX_RED], [0.5, VTX_PURPLE], [1, VTX_TEAL]],
        text="Revenue Impact ($M)",
        title="Revenue distribution — P10 / Expected / P90",
    )
    fig4.update_traces(texttemplate="%{text:+.0f}M", textposition="outside")
    fig4.update_layout(
        height=210, margin=dict(l=0, r=70, t=36, b=0),
        showlegend=False, coloraxis_showscale=False,
        plot_bgcolor="white", paper_bgcolor="white", font=CHART_FONT,
        title_font=dict(size=13, color=VTX_PURPLE_DARK),
        xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="rgba(0,0,0,0.2)"),
        yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig4, use_container_width=True)

    callout(f"💡 <b>AI Simulation Summary:</b> {wi['insight']}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — AI INSIGHTS CHAT
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    section("💬", "AI Insights Chat",
            "Ask questions about the forecast, inventory, scenarios, or methodology")

    QA_PAIRS = {
        "forecast accuracy": (
            "Our demand forecast achieves <b>94.1% accuracy</b> (MAPE basis), vs the industry "
            "average of ~85% for specialty pharma. The model combines a gradient-boosted "
            "time-series base with leading indicator overlays — payer coverage, physician "
            "awareness, and diagnosis rates — updated weekly from specialty pharmacy sell-through data."
        ),
        "safety stock": (
            "Traditional pharma safety stock uses a static Z-score formula recalculated quarterly. "
            "Our AI model re-runs optimization continuously, handles non-normal demand distributions "
            "(critical for rare disease populations), and optimizes across the full supply network. "
            "Result: <b>18–25% reduction in holding costs</b> with equal or better service levels."
        ),
        "trikafta": (
            "Trikafta is currently <b>at reorder threshold</b> with ~16 days on hand. "
            "The AI model recommends initiating a PO for <b>14,000 units</b> based on the current "
            "service level target (96%) and CMO lead time of 21 days. Q3 demand is projected at "
            "<b>48,200 scripts</b>, up 12% vs Q2, driven primarily by payer coverage expansion."
        ),
        "symdeko": (
            "⚠️ Symdeko is currently <b>below minimum stock</b> at ~12 days on hand vs a 15-day "
            "minimum threshold. An immediate order of <b>8,200 units</b> is recommended. Despite "
            "lower revenue contribution (11%), a stockout risks patient adherence breaks with "
            "long-term retention impact."
        ),
        "competitor": (
            "At the current <b>30% competitor FDA approval probability</b>, the expected net "
            "revenue impact is <b>+$124M</b> over 18 months — market expansion and PSP uplift "
            "more than offset the competitive drag. If probability exceeds <b>60%</b>, the model "
            "projects net impact turns negative without a defensive pricing or access strategy."
        ),
        "monte carlo": (
            "The scenario simulator runs <b>10,000 Monte Carlo iterations</b> per configuration. "
            "Each lever is modeled as a probability distribution — competitor approval as binomial, "
            "others as truncated normals. Revenue outcomes are aggregated into P10/Expected/P90 "
            "estimates, giving a distribution of outcomes rather than a single-point estimate."
        ),
        "roi": (
            "Estimated ROI from AI-driven analytics vs. static models: <b>$3.1M in inventory "
            "carrying cost savings</b> annually, ~<b>6% improvement in forecast accuracy</b> "
            "(reducing over- and under-supply costs), and faster response to demand signals "
            "(weekly vs. quarterly replan cycles). For a portfolio of Vertex's scale, total "
            "value impact is estimated at <b>$8–12M annually</b>."
        ),
        "kalydeco": (
            "Kalydeco is in a <b>healthy inventory position</b> at ~131 days on hand with stable "
            "demand trends. Forecast accuracy is 91%. No immediate action required — the AI model "
            "recommends maintaining current reorder cadence and monitoring for any label expansion "
            "signals that could shift demand."
        ),
        "payer": (
            "Payer coverage expansion is the <b>highest-leverage demand driver</b> in the model. "
            "A 10pp increase in formulary coverage drives approximately +6,800 incremental scripts "
            "over 6 months for Trikafta. The model tracks both commercial and government payer "
            "signals, including prior authorization removal and step-edit policy changes."
        ),
    }

    def get_ai_response(question: str) -> str:
        q_lower = question.lower()
        for key, answer in QA_PAIRS.items():
            if key in q_lower:
                return answer
        return (
            f"Thanks for asking about <i>\"{question}\"</i>. Based on the current model: "
            f"Q3 demand is tracking at <b>48,200 scripts</b> (+12% YoY), safety stock is "
            f"optimized to <b>42 days</b> at 96% service level, and the base-case scenario "
            f"projects <b>+$124M</b> revenue impact over 18 months.<br><br>"
            f"Try asking about: <i>forecast accuracy, safety stock, Trikafta, Symdeko, "
            f"Kalydeco, payer coverage, competitor risk, Monte Carlo, or ROI.</i>"
        )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            ("ai",
             "👋 Hi! I'm your Vertex AI Analytics assistant. Ask me anything about the "
             "demand forecast, inventory recommendations, or scenario simulations.<br><br>"
             "Try: <i>'Why is Symdeko at risk?'</i> · "
             "<i>'What drives forecast accuracy?'</i> · "
             "<i>'What's the ROI of AI analytics?'</i>")
        ]

    # Suggested prompts
    st.markdown("**Suggested questions:**")
    p1, p2, p3, p4 = st.columns(4)
    suggestions = [
        "What drives forecast accuracy?",
        "Why is Symdeko at risk?",
        "Explain Monte Carlo simulation",
        "What's the ROI of AI analytics?",
    ]
    for col, sug in zip([p1, p2, p3, p4], suggestions):
        if col.button(sug, use_container_width=True):
            st.session_state.chat_history.append(("user", sug))
            st.session_state.chat_history.append(("ai", get_ai_response(sug)))
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Chat history
    for role, msg in st.session_state.chat_history:
        css = "chat-msg-ai" if role == "ai" else "chat-msg-user"
        st.markdown(f"<div class='{css}'>{msg}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Input row
    col_in, col_btn = st.columns([5, 1])
    with col_in:
        user_input = st.text_input(
            "Message", label_visibility="collapsed",
            placeholder="e.g. How does AI safety stock differ from traditional formulas?",
            key="chat_input",
        )
    with col_btn:
        send = st.button("Send →", use_container_width=True, type="primary")

    if send and user_input.strip():
        st.session_state.chat_history.append(("user", user_input.strip()))
        st.session_state.chat_history.append(("ai", get_ai_response(user_input.strip())))
        st.rerun()

    if st.button("Clear chat", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vtx-footer">
    VERTEX PHARMACEUTICALS &nbsp;·&nbsp; AI Predictive Analytics Prototype &nbsp;·&nbsp;
    All figures are illustrative model outputs, not actual Vertex Pharmaceuticals data.
    &nbsp;·&nbsp; Built with Streamlit &amp; Plotly
</div>
""", unsafe_allow_html=True)
