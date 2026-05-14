# Vertex Pharma · AI Predictive Analytics Prototype

A Streamlit prototype demonstrating AI-driven predictive analytics for pharma — demand forecasting, inventory optimization, and what-if scenario simulation.

---

## Features

| Tab | What it shows |
|-----|--------------|
| **Demand Forecast** | 12-month script volume forecast with leading indicator sliders (payer coverage, physician awareness, diagnosis rate) and 95% confidence bands |
| **Inventory Optimizer** | AI safety stock recommendations, service level vs. carrying cost tradeoff curve, and SKU-level reorder table |
| **What-If Simulation** | Monte Carlo scenario engine (10k runs) across competitor approval probability, market expansion, PSP uplift, and price sensitivity |

---

## Quickstart (local)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/vertex-analytics.git
cd vertex-analytics

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in.
3. Click **New app** → select your repo → set **Main file path** to `app.py`.
4. Click **Deploy**. That's it — no extra config needed.

> **Tip:** For a private repo, Streamlit Cloud will prompt you to authorize GitHub access during setup.

---

## File structure

```
vertex-analytics/
├── app.py              # Streamlit UI — tabs, charts, controls
├── models.py           # Forecast, inventory, and simulation logic
├── data.py             # Sample data, constants, default parameters
├── requirements.txt    # Python dependencies
└── README.md
```

---

## Customizing for real data

| What to change | Where |
|----------------|-------|
| Product names and SKUs | `data.py → PRODUCTS` |
| Historical script actuals | `data.py → ACTUAL_SCRIPTS` |
| Baseline forecast values | `data.py → BASE_FORECAST` |
| Model coefficients (payer uplift, PSP effect, etc.) | `models.py` — each function has inline comments |
| Default slider values | `data.py → DEFAULT_PARAMS` |

For production data connections (Snowflake, S3, internal APIs), replace the constants in `data.py` with live queries using `@st.cache_data` to avoid re-fetching on every slider interaction.

---

## Notes

- All figures are illustrative model outputs, not actual Vertex Pharmaceuticals data.
- The Monte Carlo simulation uses `numpy.random.default_rng(42)` for reproducibility — remove the seed for live stochastic runs.
- Charts use Plotly for hover tooltips and confidence bands. Chart sizing is responsive via `use_container_width=True`.
