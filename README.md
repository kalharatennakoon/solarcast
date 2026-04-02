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

Raw data lives in [backend/data/](backend/data/) as yearly CSV summaries (not tracked in git — local only).

## Tech Stack

| Layer | Technology |
|---|---|
| ML / Forecasting | Prophet (Meta) + scikit-learn |
| Data | pandas, numpy |
| API | FastAPI + uvicorn |
| Frontend | React + Recharts |
| Storage | CSV files |

## Project Structure

```
solar-predictor/
├── backend/
│   ├── api/                    # FastAPI app and route handlers
│   │   └── routes/             # /history, /predict, /train endpoints
│   ├── model/                  # ML model scripts
│   │   ├── preprocess.py       # Data loading and cleaning
│   │   ├── train.py            # Model training (Prophet)
│   │   ├── predict.py          # Prediction pipeline
│   │   ├── evaluate.py         # MAE / RMSE evaluation
│   │   └── saved_models/       # Trained model artefacts (not tracked)
│   ├── data/                   # Historical CSV files (not tracked)
│   ├── notebooks/              # EDA and model experiments
│   ├── tests/                  # pytest + httpx tests
│   └── requirements.txt
├── frontend/                   # React + Recharts dashboard
├── docs/                       # Project documentation
└── PLAN.md
```

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

API runs at `http://localhost:8000` — visit `/docs` for the interactive API reference.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### Train the model

With the backend running, click **Train Model** in the dashboard, or call the API directly:

```bash
curl -X POST http://localhost:8000/train
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/history` | All historical records grouped by year |
| GET | `/predict?months=1` | Predictions for next 1 / 3 / 6 / 12 months |
| POST | `/train` | Train the Prophet model on historical data |
| GET | `/status` | Whether the model has been trained |

## Development Phases

1. **Data Preparation** — Clean CSVs, feature engineering
2. **EDA** — Seasonality and trend analysis (notebooks)
3. **Model Development** — Prophet (primary) + regression (secondary)
4. **API Backend** — REST endpoints for history and predictions
5. **Frontend Dashboard** — Charts, prediction cards, confidence intervals
6. **Testing & Refinement** — Backtesting, MAE evaluation, tuning

See [PLAN.md](PLAN.md) and [docs/ml-model.md](docs/ml-model.md) for full details.
