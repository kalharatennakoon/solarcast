# ML Model — How It Works

## Overview

- The goal is to predict **next month's solar generation (kWh)** and derive from it the **expected creditable export** and **cash received (LKR)**.
- Generation is the only value predicted directly by the ML model. All other values are **derived** from it using historical seasonal ratios.
- The model is trained on ~21 clean monthly records spanning April 2024 → March 2026.

---

## Libraries & Algorithms

| Component | Library / Algorithm | Purpose |
|---|---|---|
| Time-series forecasting | [Prophet](https://facebook.github.io/prophet/) (Meta) | Predicts monthly generation with yearly seasonality |
| Model serialisation | `joblib` | Saves/loads the trained Prophet model |
| Data processing | `pandas`, `numpy` | Preprocessing, feature engineering, ratio computation |
| Evaluation | Custom (`evaluate.py`) | MAE, RMSE, MAPE on held-out test set |

---

## Data Used

### Raw source
- `data/2024-summary.csv`, `data/2025-summary.csv`, `data/2026-summary.csv`

### Preprocessing rules applied before training

- **Feb 2024 (26–29 Feb):** System was installed at end of February. Only 4 days of data — excluded entirely.
- **Feb–Mar 2024 merged pair:** Because Feb is excluded and the two months share one CEB reading, the entire pair is discarded. CEB values cannot be cleanly separated.
- **All other merged pairs** (Apr–May 2024, Jan–Feb 2025, Jan–Feb 2026): Split into **two separate records**, one per month.
  - Each month keeps its own real generation value (recorded individually by the inverter)
  - Export, Import, Creditable Export, Cash = combined CEB reading ÷ 2 (50/50 split)
  - This ensures every month has a training record — previously months like February had zero data, causing the model to predict 0 kWh
- **Mar 2026:** Included for generation training (816 kWh confirmed). Cash is excluded from cash-related ratio computation (not yet received at time of training).
- Records with no creditable export value are dropped from the full pipeline training.

### Clean training records (after preprocessing)

| # | Record | Generation (kWh) | Creditable Export (kWh) | Type |
|---|---|---|---|---|
| 1 | Apr–May 2024 avg | 638.5 | 561.0 | Merged avg |
| 2 | Jun 2024 | 580 | 438 | Standalone |
| 3 | Jul 2024 | 595 | 506 | Standalone |
| 4 | Aug 2024 | 590 | 531 | Standalone |
| 5 | Sep 2024 | 600 | 441 | Standalone |
| 6 | Oct 2024 | 593 | 489 | Standalone |
| 7 | Nov 2024 | 475 | 475 | Standalone |
| 8 | Dec 2024 | 518 | 298 | Standalone |
| 9 | Jan–Feb 2025 avg | 558.0 | 504.0 | Merged avg |
| 10 | Mar 2025 | 690 | 552 | Standalone |
| 11 | Apr 2025 | 675 | 598 | Standalone |
| 12 | May 2025 | 612 | 495 | Standalone |
| 13 | Jun 2025 | 608 | 458 | Standalone |
| 14 | Jul 2025 | 622 | 509 | Standalone |
| 15 | Aug 2025 | 634 | 569 | **← last training record** |
| 16 | Sep 2025 | 568 | 471 | **← test set starts** |
| 17 | Oct 2025 | 567 | 319 | Test |
| 18 | Nov 2025 | 437 | 381 | Test |
| 19 | Dec 2025 | 506 | 342 | Test |
| 20 | Jan–Feb 2026 avg | 515.0 | 416.5 | Merged avg / Test |
| 21 | Mar 2026 | 816 | 543 | Test |

**Total: 21 records — 15 training (70%) / 6 test (30%)**

> The split is **chronological** — training always precedes test. Shuffling time-series data would cause data leakage.

---

## Model 1 — Prophet (Generation Forecast)

### What Prophet does

- Prophet is a Bayesian additive regression model designed for time-series with strong seasonal patterns and limited data.
- It decomposes the signal into: `y(t) = trend(t) + seasonality(t) + noise`
- With monthly solar data, **yearly seasonality** is the dominant pattern (more sun in dry months: Jan–Apr in Sri Lanka).
- Weekly and daily seasonality are disabled (irrelevant for monthly data).

### Training input

```
ds          y
----------  ------
2024-04-01  638.5      ← averaged Apr–May merged pair
2024-06-01  580
2024-07-01  595
...
2025-08-01  634        ← last training record
```

### Key Prophet settings

| Setting | Value | Reason |
|---|---|---|
| `yearly_seasonality` | `True` | Solar generation follows annual cycles |
| `weekly_seasonality` | `False` | Monthly data — not applicable |
| `daily_seasonality` | `False` | Monthly data — not applicable |
| `interval_width` | `0.90` | 90% confidence interval on predictions |
| `seasonality_mode` | `additive` | Seasonal swings are roughly constant in magnitude |

### Output

- `yhat` — point estimate of generation (kWh)
- `yhat_lower` — lower bound of 90% confidence interval
- `yhat_upper` — upper bound of 90% confidence interval

---

## Model 2 — Seasonal Ratio Tables (Derived Metrics)

Instead of a separate ML model for export/cash, historical per-month ratios are computed from the training set and stored. This is intentional — the relationship between generation and export is stable and seasonal, making a ratio-based approach both simpler and more interpretable than a black-box regression.

### Export ratio

For each calendar month m:

```
export_ratio[m] = mean( export[i] / generation[i] )   for all training records in month m
```

- Captures seasonality: e.g., January tends to have a high export ratio because the CEB reading covers the combined Jan+Feb period.

### Import average

```
import_avg[m] = mean( import_kwh[i] )   for all training records in month m
```

- Import (grid consumption) is relatively stable and seasonal. Using the monthly average is a reasonable estimate.

---

## Prediction Pipeline (Step-by-Step)

Given a target month with calendar month number `m`:

### Step 1 — Predict generation

```
gen       = Prophet.yhat          (point estimate)
gen_lower = Prophet.yhat_lower    (90% CI lower)
gen_upper = Prophet.yhat_upper    (90% CI upper)
```

### Step 2 — Derive export

```
ratio      = export_ratio[m]           (seasonal mean ratio)
ratio_std  = export_ratio_std[m]       (standard deviation of ratio)

export       = gen       × ratio
export_lower = gen_lower × max(ratio − 1.5 × ratio_std, 0)
export_upper = gen_upper × (ratio + 1.5 × ratio_std)
```

> The 1.5 × std multiplier gives approximately 87% coverage of the ratio distribution.

### Step 3 — Derive import

```
import_est = import_avg[m]    (historical monthly average, point estimate)
```

### Step 4 — Creditable export

```
creditable_export       = max(export       − import_est, 0)
creditable_export_lower = max(export_lower − import_est, 0)
creditable_export_upper = max(export_upper − import_est, 0)
```

> Clamped to zero — creditable export cannot be negative.

### Step 5 — Cash (LKR)

```
cash       = creditable_export       × 37
cash_lower = creditable_export_lower × 37
cash_upper = creditable_export_upper × 37
```

> LKR 37 per kWh is the fixed CEB rate for creditable export.

---

## Confidence Intervals

- Generation confidence comes directly from Prophet's Bayesian posterior — it reflects both trend uncertainty and seasonal uncertainty.
- Export and cash confidence additionally incorporate the **variability in the historical export/generation ratio** for that calendar month.
- Wider intervals in months with fewer historical observations (e.g. month 2 — only one Feb in training data).
- All intervals are **90% confidence intervals**.
- The UI displays confidence as a range (`lower – upper`) and a `±N%` badge (half-width relative to the point estimate).

---

## Evaluation Metrics

Run `python model/evaluate.py` after training to see:

| Metric | Description |
|---|---|
| **MAE** | Mean Absolute Error — average kWh error per month |
| **RMSE** | Root Mean Squared Error — penalises large errors more than MAE |
| **MAPE** | Mean Absolute Percentage Error — percentage error, scale-independent |

---

## How to Retrain

```bash
cd model
python train.py       # trains and saves model artefacts to saved_models/
python evaluate.py    # evaluates on the test set
python predict.py 3   # prints predictions for next 3 months
```

---

## Known Limitations

- **Small dataset (~21 records).** Prophet handles small datasets reasonably well due to its Bayesian priors, but predictions beyond 3–6 months carry increasing uncertainty.
- **Merged month averaging** introduces a small approximation. The averaged record is placed at the first month of the pair, which may slightly shift the learned seasonal curve.
- **Import is not predicted — it is averaged.** If your grid consumption changes significantly (e.g. new appliances, EV charging), the model will underestimate or overestimate creditable export.
- **The LKR 37/unit rate is hardcoded.** If the CEB rate changes, `RATE_PER_UNIT` in `predict.py` must be updated.
- **Cash received ≠ Total cash.** The model predicts Total Cash (creditable export × 37). The actual cash received after service fees and taxes will be slightly lower. The model does not currently predict the deduction amount.
- **No weather data.** Adding weather features (sunshine hours, cloud cover) would improve accuracy significantly once more data accumulates.

---

## What the UI Shows vs. What the Model Produces

| UI element | Source |
|---|---|
| Prediction cards (value + range) | `predict.py` → FastAPI `/predict` endpoint → React |
| `±N%` confidence badge | Half-width of Prophet 90% CI relative to point estimate |
| "Model not trained" badge | API returns model status; `train.py` must be run first |
| Historical chart & tables | Historical CSV data via FastAPI `/history` endpoint |
