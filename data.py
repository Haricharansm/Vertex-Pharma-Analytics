"""
data.py — Sample data and constants for Vertex Pharma Analytics prototype.
Replace with real data connections (Snowflake, S3, etc.) in production.
"""

import pandas as pd
import numpy as np

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

QUARTERS = ["Q3 '25", "Q4 '25", "Q1 '26", "Q2 '26", "Q3 '26", "Q4 '26"]

# Actual historical scripts (Jan–Jun), None = future
ACTUAL_SCRIPTS = [38200, 39100, 40500, 41200, 42800, 44100,
                  None, None, None, None, None, None]

# Baseline forecast (Jun anchor + Jul–Dec projection)
BASE_FORECAST = [None, None, None, None, None, 44100,
                 45800, 48200, 50100, 51800, 53200, 55000]

# Confidence interval bands
UPPER_CI = [None, None, None, None, None, 44100,
            47900, 50300, 52400, 54200, 55700, 57500]

LOWER_CI = [None, None, None, None, None, 44100,
            43700, 46100, 47800, 49400, 50700, 52500]

# Product portfolio
PRODUCTS = [
    {
        "name": "Trikafta 200/150/100mg",
        "sku": "VTX-001",
        "current_stock": 18500,
        "reorder_point": 14000,
        "min_stock": 8000,
        "lead_time": 21,
        "avg_daily_demand": 1150,
    },
    {
        "name": "Kalydeco 150mg",
        "sku": "VTX-002",
        "current_stock": 42000,
        "reorder_point": 12000,
        "min_stock": 6000,
        "lead_time": 18,
        "avg_daily_demand": 320,
    },
    {
        "name": "Symdeko 100/150mg",
        "sku": "VTX-003",
        "current_stock": 5800,
        "reorder_point": 9000,
        "min_stock": 7000,
        "lead_time": 24,
        "avg_daily_demand": 480,
    },
    {
        "name": "Orkambi 200/125mg",
        "sku": "VTX-004",
        "current_stock": 31000,
        "reorder_point": 11000,
        "min_stock": 5500,
        "lead_time": 20,
        "avg_daily_demand": 410,
    },
]

# Service level → Z-score lookup
Z_SCORES = {
    90: 1.28, 91: 1.34, 92: 1.41, 93: 1.48,
    94: 1.56, 95: 1.65, 96: 1.75, 97: 1.88,
    98: 2.05, 99: 2.33,
}

# What-if scenario base quarterly volumes ('000s scripts)
BASE_QUARTERLY = [44, 46, 48, 50, 52, 54]

# Forecast model default parameters
DEFAULT_PARAMS = {
    "payer_coverage": 15,
    "physician_awareness": 72,
    "diag_rate": 230,
    "service_level": 96,
    "lead_time_var": 5,
    "demand_cv": 18,
    "competitor_prob": 30,
    "new_markets": 2,
    "psp_uplift": 20,
    "price_elasticity": 10,
}
