# Solar Predictor — Project Plan

## Overview

A machine learning tool that predicts **next month's solar energy generation** and **expected cash received** based on historical data from the solar system dashboard. The model is trained on data from 2024, 2025, and early 2026.

---

## Data Understanding

From the dashboard, each monthly record contains:

| Column | Description |
|---|---|
| Total Generation (kWh) | Solar energy generated that month |
| Total Export to CEB (kWh) | Energy sent back to the grid |
| Total Import from CEB (kWh) | Energy consumed from the grid |
| Creditable Export (kWh) | Net export (Export − Import) |
| Total Cash (LKR 37/unit) | Theoretical max payout |
| Cash Received (LKR) | Actual payout received |

**Rate:** LKR 37/- per unit (kWh) of creditable export.

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Language | Python 3.11+ | Best ML/data ecosystem |
| ML / Forecasting | Prophet (Meta) + scikit-learn | Prophet handles seasonality well with limited data (~26 months); scikit-learn for feature-based models |
| Data handling | pandas, numpy | Standard data manipulation |
| API Backend | FastAPI | Lightweight, async, auto-docs |
| Frontend | React + Recharts | Clean dashboard with charts |
| Data storage | CSV files | Simple, no server needed, sufficient for monthly data |

---

## Project Structure

```
solar-prediction-app/
├── data/
│   └── solar_data.csv          # Historical monthly data (to be populated)
│
├── notebooks/
│   └── 01_eda.ipynb             # Exploratory Data Analysis
│   └── 02_model_experiments.ipynb
│
├── model/
│   ├── preprocess.py            # Data cleaning & feature engineering
│   ├── train.py                 # Model training script
│   ├── predict.py               # Prediction logic
│   ├── evaluate.py              # Model evaluation & metrics
│   └── saved_models/            # Serialized trained models
│
├── api/
│   ├── main.py                  # FastAPI app entry point
│   └── routes/
│       ├── predict.py           # POST /predict endpoint
│       └── history.py           # GET /history endpoint
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── Dashboard.jsx    # Main dashboard
│       │   ├── PredictionCard.jsx
│       │   └── HistoryChart.jsx
│
├── tests/
│   ├── test_model.py
│   └── test_api.py
│
├── requirements.txt
├── .env.example
└── PLAN.md
```

---

## Development Phases

### Phase 1 — Data Preparation
**Goal:** Get all historical data into a clean, structured CSV.

- Create `data/solar_data.csv` with columns: `year`, `month`, `total_generation_kwh`, `total_export_kwh`, `total_import_kwh`, `creditable_export_kwh`, `total_cash_lkr`, `cash_received_lkr`
- Handle the Feb 2024 partial month (26–29 Feb) — annotate or exclude from training
- Handle merged rows (e.g., Feb+March export to CEB shared in the dashboard)
- Add engineered features: `month_num`, `season`, `year_index`, `days_in_month`

### Phase 2 — Exploratory Data Analysis (Notebook)
**Goal:** Understand seasonality, trends, and correlations.

- Plot monthly generation over time
- Check seasonal patterns (solar is stronger in dry months in Sri Lanka)
- Correlation between generation → export → cash received
- Identify any anomalies or outliers

### Phase 3 — Model Development
**Goal:** Train and evaluate prediction models.

Two complementary models:

**Model A — Prophet (Primary)**
- Input: time series of `total_generation_kwh` indexed by month
- Automatically handles yearly seasonality
- Outputs: forecast for next 1–3 months with confidence intervals

**Model B — Feature-Based Regression (Secondary)**
- Input features: `month_num`, `year`, `season`, lagged values (last month's generation, last year same month)
- Models: Random Forest Regressor, XGBoost
- More interpretable, good for "what if" analysis

**Prediction pipeline:**
1. Predict `total_generation_kwh`
2. Derive `total_export_kwh` based on historical export/generation ratio per season
3. Derive `creditable_export_kwh = export − import` (import is relatively stable)
4. Calculate `predicted_cash = creditable_export × 37`

### Phase 4 — API Backend
**Goal:** Expose predictions via a REST API.

**Endpoints:**
- `GET /history` — Returns all historical data
- `POST /predict` — Returns prediction for a given future month
- `GET /predict/next` — Auto-predicts the upcoming month

### Phase 5 — Frontend Dashboard
**Goal:** Visual interface for viewing history and predictions.

- Line chart of historical generation over time
- Highlighted prediction for next month
- Confidence interval band on the chart
- Cards showing: Predicted Generation, Predicted Export, Predicted Cash Received

### Phase 6 — Testing & Refinement
- Backtest model: train on 2024 data, predict 2025, compare actual vs predicted
- Calculate MAE (Mean Absolute Error) on the test set
- Tune model parameters, retrain on full dataset

---

## Data Entry — Next Step

Before any code runs, we need the data in a CSV. The suggested format is:

```
year,month,month_num,total_generation_kwh,total_export_kwh,total_import_kwh,creditable_export_kwh,total_cash_lkr,cash_received_lkr
2024,February,2,937,792,69,723,26751,25414.40
2024,March,3,...
...
```

You can either:
1. **Manually enter** the 2024, 2025, and 2026 data into `data/solar_data.csv`, or
2. **Share the full data** (screenshot, Excel, or typed values) and I can build the CSV for you.

---

## Starting Point Recommendation

1. Populate `data/solar_data.csv` with all your data
2. I'll build Phase 1 (preprocessing) + Phase 3 (model) as Python scripts first
3. Then wire up the FastAPI backend
4. Then build the React dashboard

This gives you a working prediction engine quickly before investing in the full UI.
