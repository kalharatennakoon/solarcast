"""
train.py
--------
Trains the solar prediction model and saves all artefacts to
model/saved_models/.

Models trained
--------------
1. Prophet (primary) — forecasts monthly solar generation with yearly
   seasonality. Provides confidence intervals natively.

2. Seasonal ratio tables (derived) — instead of a second ML model for
   export/cash, we compute per-month historical ratios from the training
   set:
     export_ratio[month]  = mean(export / generation)
     import_avg[month]    = mean(import_kwh)
   These are used in predict.py to derive creditable export and cash
   from the predicted generation value.

Split: 70% training / 30% test (chronological order, never shuffled).
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from prophet import Prophet

from model.preprocess import preprocess, train_test_split

MODELS_DIR = Path(__file__).parent / "saved_models"
MODELS_DIR.mkdir(exist_ok=True)


def compute_seasonal_ratios(train_df: pd.DataFrame) -> dict:
    """
    For each calendar month (1–12) compute:
      - mean and std of (export / generation) ratio
      - mean and std of import_kwh

    Months with no training data use the overall mean as fallback.
    """
    ratios = {}
    for month_num in range(1, 13):
        subset = train_df[train_df["month_num"] == month_num]
        if len(subset) == 0:
            # Fallback: overall mean
            ratios[month_num] = {
                "export_ratio_mean": float(
                    (train_df["export"] / train_df["generation"]).mean()
                ),
                "export_ratio_std": float(
                    (train_df["export"] / train_df["generation"]).std()
                ),
                "import_mean": float(train_df["import_kwh"].mean()),
                "import_std": float(train_df["import_kwh"].std()),
                "generation_mean": float(train_df["generation"].mean()),
                "generation_std": float(train_df["generation"].std()),
                "n": 0,
            }
        else:
            export_ratios = subset["export"] / subset["generation"]
            ratios[month_num] = {
                "export_ratio_mean": float(export_ratios.mean()),
                "export_ratio_std": float(export_ratios.std()),
                "import_mean": float(subset["import_kwh"].mean()),
                "import_std": float(subset["import_kwh"].std()),
                "generation_mean": float(subset["generation"].mean()),
                "generation_std": float(subset["generation"].std()),
                "n": len(subset),
            }
    return ratios


def train():
    df = preprocess()
    train_df, test_df = train_test_split(df, train_ratio=0.70)

    print(f"Training records : {len(train_df)}")
    print(f"  {train_df['ds'].min().strftime('%b %Y')} → {train_df['ds'].max().strftime('%b %Y')}")
    print(f"Test records     : {len(test_df)}")
    print(f"  {test_df['ds'].min().strftime('%b %Y')} → {test_df['ds'].max().strftime('%b %Y')}")

    # ── Prophet — solar generation forecast ──────────────────────────────
    prophet_df = train_df[["ds", "generation"]].rename(columns={"generation": "y"})

    model = Prophet(
        growth="flat",              # solar output has no long-term trend —
                                    # predictions based purely on seasonality.
                                    # Using linear/logistic growth caused
                                    # unrealistic extrapolation (e.g. Sep 2026
                                    # predicted at 1,100+ kWh).
        yearly_seasonality=True,
        weekly_seasonality=False,   # monthly data — weekly irrelevant
        daily_seasonality=False,
        interval_width=0.90,        # 90% confidence interval
        seasonality_mode="additive",
    )
    model.fit(prophet_df)

    model_path = MODELS_DIR / "prophet_generation.pkl"
    joblib.dump(model, model_path)
    print(f"\nProphet model saved → {model_path}")

    # ── Seasonal ratio tables ─────────────────────────────────────────────
    ratios = compute_seasonal_ratios(train_df)
    ratios_path = MODELS_DIR / "seasonal_ratios.json"
    with open(ratios_path, "w") as f:
        json.dump(ratios, f, indent=2)
    print(f"Seasonal ratios saved → {ratios_path}")

    # ── Save test set for evaluate.py ────────────────────────────────────
    test_path = MODELS_DIR / "test_set.csv"
    test_df.to_csv(test_path, index=False)
    print(f"Test set saved → {test_path}")

    return model, ratios


if __name__ == "__main__":
    train()
