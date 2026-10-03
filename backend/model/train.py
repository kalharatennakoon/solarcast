"""
train.py
--------
Trains the solar prediction model and saves all artefacts to the models
folder (SOLARCAST_MODELS_DIR, default model/saved_models/).

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

from dataclasses import dataclass

import pandas as pd
from prophet import Prophet

from model.artefacts import models_dir, save_artefacts
from model.preprocess import preprocess, train_test_split


@dataclass(frozen=True)
class TrainingSummary:
    training_records: int
    test_records: int
    train_period: str
    test_period: str
    trained_at: str


def _period(df: pd.DataFrame) -> str:
    return f"{df['ds'].min().strftime('%b %Y')} → {df['ds'].max().strftime('%b %Y')}"


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


def train() -> TrainingSummary:
    df = preprocess()
    train_df, test_df = train_test_split(df, train_ratio=0.70)

    print(f"Training records : {len(train_df)}")
    print(f"  {_period(train_df)}")
    print(f"Test records     : {len(test_df)}")
    print(f"  {_period(test_df)}")

    # ── Prophet — solar generation forecast ──────────────────────────────
    prophet_df = train_df[["ds", "generation"]].rename(columns={"generation": "y"})

    model = Prophet(
        growth="flat",              # solar output has no long-term trend —
                                    # predictions based purely on seasonality.
                                    # Using linear/logistic growth caused
                                    # unrealistic extrapolation (e.g. Sep 2026
                                    # predicted at 1,100+ kWh).
        yearly_seasonality=3,       # fourier_order=3 (6 terms) instead of the
                                    # default 10 (20 terms). With only ~16
                                    # training records, fourier_order=10 severely
                                    # overfits — producing Jan=274, Aug=264 kWh
                                    # predictions vs actuals of 512/634 kWh.
                                    # order=3 captures the dominant annual cycle
                                    # without fitting noise.
        n_changepoints=0,           # changepoints are irrelevant with growth='flat'
                                    # and cause overfitting on small datasets.
        weekly_seasonality=False,   # monthly data — weekly irrelevant
        daily_seasonality=False,
        interval_width=0.90,        # 90% confidence interval
        seasonality_mode="additive",
    )
    model.fit(prophet_df)

    # ── Seasonal ratio tables ─────────────────────────────────────────────
    ratios = compute_seasonal_ratios(train_df)

    # ── Persist model, ratios, test set and timestamp (newest first) ─────
    trained_at = save_artefacts(model, ratios, test_df)
    print(f"\nArtefacts saved → {models_dir()}")
    print(f"Trained at: {trained_at}")

    return TrainingSummary(
        training_records=len(train_df),
        test_records=len(test_df),
        train_period=_period(train_df),
        test_period=_period(test_df),
        trained_at=trained_at,
    )


if __name__ == "__main__":
    train()
