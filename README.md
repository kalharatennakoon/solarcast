# Solar Predictor

A machine learning tool that predicts next month's solar energy generation and expected cash received, based on historical data from a residential solar system in Sri Lanka.

## What it does

- Forecasts monthly solar generation (kWh) using time-series ML (Prophet + scikit-learn)
- Predicts creditable export and expected cash payout at LKR 37/unit
- Exposes predictions via a FastAPI REST API
- Displays history and forecasts in a React dashboard

## Data

Historical monthly records from Feb 2024 onwards, sourced from the solar system dashboard:

| Field | Description |
|---|---|
| Total Generation (kWh) | Solar energy generated that month |
| Total Export to CEB (kWh) | Energy sent back to the grid |
| Total Import from CEB (kWh) | Energy consumed from the grid |
| Creditable Export (kWh) | Net export (Export − Import) |
| Cash Received (LKR) | Actual payout at LKR 37/unit |

Raw data lives in [data/](data/) as yearly CSV summaries.

## Tech Stack

| Layer | Technology |
|---|---|
| ML / Forecasting | Prophet (Meta) + scikit-learn, XGBoost |
| Data | pandas, numpy |
| API | FastAPI + uvicorn |
| Frontend | React + Recharts |
| Storage | CSV files |

## Project Structure

```
solar-predictor/
├── data/                   # Historical CSV data by year
├── notebooks/              # EDA and model experiments
├── model/                  # Preprocessing, training, prediction scripts
│   └── saved_models/       # Serialized trained models (not tracked)
├── api/                    # FastAPI backend
├── frontend/               # React dashboard
├── tests/                  # pytest + httpx tests
├── requirements.txt
└── PLAN.md                 # Detailed project plan
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn api.main:app --reload
```

## Development Phases

1. **Data Preparation** — Clean CSVs, feature engineering
2. **EDA** — Seasonality and trend analysis (notebooks)
3. **Model Development** — Prophet (primary) + regression (secondary)
4. **API Backend** — REST endpoints for history and predictions
5. **Frontend Dashboard** — Charts, prediction cards, confidence intervals
6. **Testing & Refinement** — Backtesting, MAE evaluation, tuning

See [PLAN.md](PLAN.md) for full details.
