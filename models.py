"""
models.py — Predictive analytics models for Vertex Pharma prototype.

Three modules:
  1. run_forecast()     — demand forecasting with leading indicators
  2. run_inventory()    — AI-driven safety stock optimization
  3. run_whatif()       — Monte Carlo scenario simulation
  4. build_tradeoff_curve() — service level vs safety stock curve
  5. get_reorder_table()    — SKU-level reorder recommendations
"""

import numpy as np
import pandas as pd
from scipy.stats import norm

from data import (
    MONTHS, QUARTERS, ACTUAL_SCRIPTS, BASE_FORECAST,
    UPPER_CI, LOWER_CI, PRODUCTS, Z_SCORES, BASE_QUARTERLY,
)


# ──────────────────────────────────────────────
# 1. DEMAND FORECAST
# ──────────────────────────────────────────────

def run_forecast(payer: int, awareness: int, diag_rate: int) -> dict:
    """
    Adjust 12-month demand forecast based on leading indicators.

    Parameters
    ----------
    payer       : payer coverage expansion % (0–30)
    awareness   : physician awareness index (50–100)
    diag_rate   : new diagnosis rate per month (100–400)

    Returns
    -------
    dict with:
        df              — DataFrame for charting
        q3_scripts      — projected Q3 total scripts
        nps             — new patient starts
        insight         — narrative string
    """
    multiplier = (
        1
        + (payer - 15) * 0.004
        + (awareness - 72) * 0.003
        + (diag_rate - 230) * 0.0015
    )
    multiplier = max(0.7, min(1.5, multiplier))

    forecast = [
        round(v * multiplier) if v is not None else None
        for v in BASE_FORECAST
    ]
    upper = [
        round(v * multiplier * 1.044) if v is not None else None
        for v in BASE_FORECAST
    ]
    lower = [
        round(v * multiplier * 0.958) if v is not None else None
        for v in BASE_FORECAST
    ]

    df = pd.DataFrame({
        "Month": MONTHS,
        "Actual": ACTUAL_SCRIPTS,
        "Forecast": forecast,
        "Upper CI (95%)": upper,
        "Lower CI (95%)": lower,
    })

    q3_scripts = forecast[7]  # August as Q3 midpoint proxy
    nps = round(1840 * (1 + (payer - 15) * 0.003 + (diag_rate - 230) * 0.001))
    nps = max(500, nps)

    payer_scripts = round(abs(payer - 15) * 680)
    if payer > 15:
        payer_txt = f"Payer coverage ({payer}%) adds ~{payer_scripts:,} scripts vs baseline."
    elif payer < 15:
        payer_txt = f"Payer coverage ({payer}%) removes ~{payer_scripts:,} scripts vs baseline."
    else:
        payer_txt = "Payer coverage is at baseline."

    if awareness >= 80:
        aware_txt = f"Physician awareness at {awareness} is strong — diminishing returns above 85."
    else:
        aware_txt = f"Physician awareness at {awareness} is the highest-leverage remaining opportunity."

    insight = (
        f"Current indicators project **{q3_scripts:,} scripts in Q3**. "
        f"{payer_txt} {aware_txt}"
    )

    return {
        "df": df,
        "q3_scripts": q3_scripts,
        "nps": nps,
        "insight": insight,
    }


# ──────────────────────────────────────────────
# 2. INVENTORY OPTIMIZER
# ──────────────────────────────────────────────

def run_inventory(svc_level: int, lead_time_var: int, demand_cv_pct: int) -> dict:
    """
    Calculate optimal safety stock using AI-calibrated parameters.

    Parameters
    ----------
    svc_level      : target service level % (90–99)
    lead_time_var  : lead time standard deviation in days (1–14)
    demand_cv_pct  : demand coefficient of variation × 100 (5–40)

    Returns
    -------
    dict with ss_days, savings, stockout_risk, insight
    """
    z = Z_SCORES.get(svc_level, norm.ppf(svc_level / 100))
    avg_demand = 1150  # units/day (Trikafta primary)
    cv = demand_cv_pct / 100

    # Safety stock formula: Z × √(σ_lt² × d̄² + lt̄ × σ_d²)
    avg_lt = 21  # days
    sigma_d = cv * avg_demand
    ss_units = z * np.sqrt(lead_time_var**2 * avg_demand**2 + avg_lt * sigma_d**2)
    ss_days = max(1, round(ss_units / avg_demand))

    baseline_ss_days = 42
    savings = (baseline_ss_days - ss_days) * 170_000  # $170k per day of inventory

    stockout_risk = round((1 - svc_level / 100) * 100, 1)

    if savings > 0:
        savings_txt = f"This saves **${savings/1e6:.1f}M** in carrying costs vs the prior static model."
    else:
        cost_increase = abs(savings)
        savings_txt = (
            f"Higher service level increases holding cost by "
            f"**${cost_increase/1e3:.0f}K** but cuts stockout risk to {stockout_risk}%."
        )

    insight = (
        f"At **{svc_level}% service level** with lead time variability ±{lead_time_var} days, "
        f"optimal safety stock is **{ss_days} days**. {savings_txt}"
    )

    return {
        "ss_days": ss_days,
        "savings": savings,
        "stockout_risk": stockout_risk,
        "insight": insight,
    }


def build_tradeoff_curve() -> pd.DataFrame:
    """Build the service level vs. safety stock tradeoff curve."""
    rows = []
    for svc in range(90, 100):
        result = run_inventory(svc, 5, 18)
        rows.append({"Service Level (%)": svc, "Safety Stock (days)": result["ss_days"]})
    return pd.DataFrame(rows).set_index("Service Level (%)")


def get_reorder_table(svc_level: int = 96, lead_time_var: int = 5) -> pd.DataFrame:
    """
    Generate reorder recommendations for all SKUs.
    Status: Healthy / At threshold / Below minimum
    """
    rows = []
    for p in PRODUCTS:
        z = Z_SCORES.get(svc_level, 1.75)
        ss = round(z * np.sqrt(
            lead_time_var**2 * p["avg_daily_demand"]**2
            + p["lead_time"] * (0.18 * p["avg_daily_demand"])**2
        ))
        reorder_qty = round((p["avg_daily_demand"] * p["lead_time"]) + ss)
        days_on_hand = round(p["current_stock"] / p["avg_daily_demand"])

        if p["current_stock"] < p["min_stock"]:
            status = "🔴 Below minimum"
        elif p["current_stock"] < p["reorder_point"]:
            status = "🟡 At threshold"
        else:
            status = "🟢 Healthy"

        rows.append({
            "Product": p["name"],
            "SKU": p["sku"],
            "Stock (units)": f"{p['current_stock']:,}",
            "Days on hand": days_on_hand,
            "Status": status,
            "Recommended order": f"{reorder_qty:,}" if p["current_stock"] <= p["reorder_point"] else "—",
        })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# 3. WHAT-IF SIMULATION
# ──────────────────────────────────────────────

def run_whatif(
    comp_prob: int,
    new_markets: int,
    psp_uplift: int,
    price_elast: int,
    n_simulations: int = 10_000,
) -> dict:
    """
    Monte Carlo what-if scenario simulation.

    Parameters
    ----------
    comp_prob    : competitor FDA approval probability % (0–100)
    new_markets  : number of new geographies (0–10)
    psp_uplift   : patient support program uplift % (0–50)
    price_elast  : price sensitivity / elasticity % (0–30)
    n_simulations: Monte Carlo runs (default 10,000)

    Returns
    -------
    dict with rev_impact, script_change, risk_level,
    confidence, scenario_df, insight
    """
    rng = np.random.default_rng(42)

    # --- Monte Carlo draws ---
    comp_realized = rng.binomial(1, comp_prob / 100, n_simulations)
    market_uplift = rng.normal(new_markets * 18, new_markets * 4, n_simulations)
    psp_effect = rng.normal(psp_uplift * 3.4, psp_uplift * 0.8, n_simulations)
    comp_drag = comp_realized * rng.normal(comp_prob * 2.1, comp_prob * 0.5, n_simulations)
    price_impact = rng.normal(-price_elast * 1.2, price_elast * 0.3, n_simulations)

    net_rev_sim = market_uplift + psp_effect - comp_drag + price_impact

    expected_rev = float(np.mean(net_rev_sim))
    p10 = float(np.percentile(net_rev_sim, 10))
    p90 = float(np.percentile(net_rev_sim, 90))
    confidence = max(50, min(99, round(81 - (comp_prob > 50) * 10 + (new_markets > 5) * 5)))

    rev_label = f"{'+'if expected_rev >= 0 else ''}${expected_rev:.0f}M"

    script_pct = (new_markets * 1.8 + psp_uplift * 0.6 - comp_prob * 0.9) / 100
    script_label = f"{'+'if script_pct >= 0 else ''}{script_pct:.1f}%"

    if comp_prob > 60 or new_markets > 7:
        risk_level = "High"
        risk_sub = "Significant supply ramp required"
    elif comp_prob > 30 or new_markets > 4:
        risk_level = "Medium"
        risk_sub = "Inventory ramp needed"
    else:
        risk_level = "Low"
        risk_sub = "Supply chain stable"

    # --- Scenario curves ---
    opt_mult = 1 + new_markets * 0.025 + psp_uplift * 0.008 - comp_prob * 0.004
    pes_mult = 1 - comp_prob * 0.007 + new_markets * 0.01 - price_elast * 0.005

    scenario_df = pd.DataFrame({
        "Quarter": QUARTERS,
        "Base case": BASE_QUARTERLY,
        "Optimistic": [round(v * opt_mult, 1) for v in BASE_QUARTERLY],
        "Pessimistic": [round(v * max(0.5, pes_mult), 1) for v in BASE_QUARTERLY],
    }).set_index("Quarter")

    # --- Narrative insight ---
    lever = "patient support program" if psp_uplift > 30 else "market expansion"
    comp_warn = (
        " **⚠️ Alert:** At this competitor probability, a defensive pricing or access "
        "strategy is critical."
        if comp_prob > 60 else ""
    )
    insight = (
        f"With **{comp_prob}% competitor approval probability** and **{new_markets} new "
        f"{'market' if new_markets == 1 else 'markets'}**, expected net revenue impact is "
        f"**{rev_label}** over 18 months (P10: ${p10:.0f}M / P90: ${p90:.0f}M). "
        f"The **{lever}** is the top upside lever.{comp_warn}"
    )

    return {
        "rev_impact": expected_rev,
        "rev_label": rev_label,
        "script_change": script_label,
        "risk_level": risk_level,
        "risk_sub": risk_sub,
        "confidence": confidence,
        "p10": p10,
        "p90": p90,
        "scenario_df": scenario_df,
        "insight": insight,
        "n_simulations": n_simulations,
    }
