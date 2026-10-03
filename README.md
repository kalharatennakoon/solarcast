# SolarCast

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
| Containers | Docker (multi-stage, non-root images), nginx, Docker Compose |
| CI | GitHub Actions — ruff, pytest, image build, Trivy scan, smoke test |
| Observability | Prometheus metrics, liveness and readiness endpoints |

## Project Structure

```
solarcast/
├── backend/
│   ├── api/                    # FastAPI app and route handlers
│   │   ├── routes/             # /history, /predict, /train, /status, /healthz, /readyz
│   │   ├── metrics.py          # Prometheus metrics and request middleware
│   │   └── model_store.py      # Loads the model once and caches it in memory
│   ├── model/                  # ML model scripts
│   │   ├── preprocess.py       # Data loading, exclusions, feature engineering
│   │   ├── train.py            # Prophet training + seasonal ratio tables
│   │   ├── predict.py          # Prediction pipeline with confidence intervals
│   │   ├── evaluate.py         # MAE / RMSE / MAPE on held-out test set
│   │   ├── artefacts.py        # Reads and writes trained artefacts (atomic writes)
│   │   └── saved_models/       # Trained model artefacts (not tracked in git)
│   ├── data/                   # Historical CSV files (not tracked in git)
│   ├── sample_data/            # Synthetic CSVs for tests, CI and demos
│   ├── tests/                  # pytest suite (runs on sample_data only)
│   ├── settings.py             # Configuration from environment variables
│   ├── Dockerfile
│   ├── requirements.in         # Direct dependencies
│   ├── requirements.txt        # Pinned lock file generated from requirements.in
│   └── requirements-dev.txt    # Test and lint tooling
├── frontend/                   # React dashboard
│   ├── Dockerfile
│   └── nginx/                  # nginx config: serves the app, proxies /api
├── scripts/smoke-test.sh       # End-to-end check of the running containers
├── docker-compose.yml
├── Makefile
├── .github/workflows/ci.yml
└── docs/
    ├── ml-model.md             # Full ML model documentation
    └── roadmap.md              # MLOps platform roadmap
```

## Quick start with Docker

```bash
docker compose up --build
```

| | |
|---|---|
| Dashboard | http://localhost:8080 |
| API reference | http://localhost:8000/docs |

The CSV files in `backend/data/` are mounted read-only into the backend
container; trained models are kept in a Docker volume. On first start, click
**Train Model** in the dashboard.

No data of your own? Run it on the synthetic sample set instead:

```bash
SOLARCAST_DATA_PATH=./backend/sample_data docker compose up --build
```

`make smoke` runs an end-to-end check against the running containers.

## Local development (without Docker)

### Backend

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r backend/requirements-dev.txt
cd backend
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

### Tests and linting

```bash
cd backend
pytest              # 35 tests, on synthetic data only
ruff check .
```

Or from the project root: `make test` and `make lint`.

## Configuration

The backend is configured through environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `SOLARCAST_DATA_DIR` | `backend/data` | Folder containing the `*-summary.csv` files |
| `SOLARCAST_MODELS_DIR` | `backend/model/saved_models` | Where trained artefacts are stored |
| `SOLARCAST_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated origins allowed to call the API |
| `SOLARCAST_RATE_PER_UNIT` | `37` | LKR paid per creditable kWh |

In Docker Compose, `SOLARCAST_DATA_PATH` chooses which host folder is mounted
as the data folder (default `./backend/data`).

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/history` | Historical records grouped by year |
| GET | `/predict?months=1` | Predictions for the next 1 to 12 months |
| POST | `/train` | Train the model on historical CSV data |
| GET | `/status` | Model status and last trained timestamp |
| GET | `/healthz` | Liveness check |
| GET | `/readyz` | Readiness check (data folder available, model state) |
| GET | `/metrics` | Prometheus metrics |

## Continuous integration

Every pull request runs [the CI workflow](.github/workflows/ci.yml): lint and
tests, a frontend build, both image builds, a Trivy vulnerability scan and an
end-to-end smoke test of the containers on synthetic data.

Pushes to `main` also publish multi-architecture images to Docker Hub, once
these are set under **Settings → Secrets and variables → Actions**:

| Kind | Name | Value |
|---|---|---|
| Variable | `DOCKERHUB_USERNAME` | Your Docker Hub username |
| Secret | `DOCKERHUB_TOKEN` | A Docker Hub access token with read and write permission |

## Model Summary

- **Algorithm:** Prophet with `yearly_seasonality=3` (Fourier order 3) and `growth='flat'`
- **Training data:** 16 records — Apr 2024 → Jul 2025 (70%)
- **Test data:** 8 records — Aug 2025 → Mar 2026 (30%)
- **Test MAPE:** ~9.5% (MAE ~53 kWh per month)
- **Confidence intervals:** 90% CI computed from historical monthly generation std; export/cash CI additionally incorporates ratio variability

See [docs/ml-model.md](docs/ml-model.md) for full model documentation, and
[docs/roadmap.md](docs/roadmap.md) for where the project is heading.
