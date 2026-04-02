# Solar Predictor

A machine learning tool that predicts monthly solar energy generation and expected cash received, based on historical data from a residential solar system in Sri Lanka.

## What it does

- Forecasts monthly solar generation (kWh) using Prophet (Meta) time-series ML with yearly seasonality
- Derives creditable export and expected cash payout at LKR 37/unit using seasonal ratio tables
- Displays 90% confidence intervals on all predictions
- Exposes predictions via a FastAPI REST API
- React dashboard with prediction cards, historical chart, and data tables

## Data

Monthly records from April 2024 onwards (Feb–Mar 2024 excluded — partial install month). Raw data lives in [backend/data/](backend/data/) as yearly CSV summaries.

| Field | Description |
|---|---|
| Total Generation (kWh) | Solar energy generated — recorded by the inverter per calendar month |
| Total Export to CEB (kWh) | Energy sent back to the grid — recorded per CEB delegate visit |
| Total Import from CEB (kWh) | Energy consumed from the grid — recorded per CEB delegate visit |
| Creditable Export (kWh) | Export − Import |
| Cash Received (LKR) | Actual payout at LKR 37/unit, received ~20–28th of the following month |

**Merged months:** When the CEB delegate skips a visit, the next reading covers two months. Those pairs are split 50/50 in the CSV and treated as separate training records.

## Tech Stack

| Layer | Technology |
|---|---|
| ML / Forecasting | Prophet (Meta) — `yearly_seasonality=3`, `growth='flat'` |
| Derived metrics | Seasonal ratio tables (export/generation per calendar month) |
| Data | pandas, numpy |
| API | FastAPI + uvicorn |
| Frontend | React + Recharts |
| Storage | CSV files |

## Project Structure

```
solar-predictor/
├── backend/
│   ├── api/                    # FastAPI app and route handlers
│   │   └── routes/             # /history, /predict, /train, /status
│   ├── model/                  # ML model scripts
│   │   ├── preprocess.py       # Data loading, exclusions, feature engineering
│   │   ├── train.py            # Prophet training + seasonal ratio tables
│   │   ├── predict.py          # Prediction pipeline with confidence intervals
│   │   ├── evaluate.py         # MAE / RMSE / MAPE on held-out test set
│   │   └── saved_models/       # Trained model artefacts (not tracked in git)
│   ├── data/                   # Historical CSV files (not tracked in git)
│   └── requirements.txt
├── frontend/                   # React dashboard
└── docs/
    └── ml-model.md             # Full ML model documentation
```

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
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

Frontend runs at `http://localhost:5173`. Vite proxies `/api/*` → `http://localhost:8000/*`.

### Train the model

With the backend running, click **Train Model** in the dashboard, or:

```bash
curl -X POST http://localhost:8000/train
```

To evaluate the model on the held-out test set:

```bash
cd backend
python -m model.evaluate
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/history` | Historical records grouped by year |
| GET | `/predict?months=1` | Predictions for next 1 / 3 / 6 / 12 months |
| POST | `/train` | Train the model on historical CSV data |
| GET | `/status` | Model status and last trained timestamp |

## Model Summary

- **Algorithm:** Prophet with `yearly_seasonality=3` (Fourier order 3) and `growth='flat'`
- **Training data:** 16 records — Apr 2024 → Jul 2025 (70%)
- **Test data:** 8 records — Aug 2025 → Mar 2026 (30%)
- **Test MAPE:** ~9.5% (MAE ~53 kWh per month)
- **Confidence intervals:** 90% CI computed from historical monthly generation std; export/cash CI additionally incorporates ratio variability

See [docs/ml-model.md](docs/ml-model.md) for full model documentation.
