"""
evaluate.py
-----------
Evaluates the trained Prophet model against the held-out test set.

Metrics reported
----------------
  MAE   Mean Absolute Error         — average absolute difference in kWh
  RMSE  Root Mean Squared Error     — penalises large errors more than MAE
  MAPE  Mean Absolute Percentage    — percentage error, scale-independent
        Error

Usage
-----
  python evaluate.py
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).parent / "saved_models"


def mae(actual, predicted):
    return np.mean(np.abs(actual - predicted))


def rmse(actual, predicted):
    return np.sqrt(np.mean((actual - predicted) ** 2))


def mape(actual, predicted):
    mask = actual != 0
    return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100


def evaluate():
    model = joblib.load(MODELS_DIR / "prophet_generation.pkl")
    test_df = pd.read_csv(MODELS_DIR / "test_set.csv", parse_dates=["ds"])

    if test_df.empty:
        print("Test set is empty — run train.py first.")
        return

    forecast = model.predict(test_df[["ds"]])

    actual    = test_df["generation"].values
    predicted = forecast["yhat"].clip(lower=0).values

    print("─" * 50)
    print("  Model Evaluation — Generation (kWh)")
    print("─" * 50)
    print(f"  Test period : {test_df['ds'].min().strftime('%b %Y')} → {test_df['ds'].max().strftime('%b %Y')}")
    print(f"  Records     : {len(test_df)}")
    print("─" * 50)
    print(f"  MAE         : {mae(actual, predicted):.1f} kWh")
    print(f"  RMSE        : {rmse(actual, predicted):.1f} kWh")
    print(f"  MAPE        : {mape(actual, predicted):.1f} %")
    print("─" * 50)
    print()

    # Per-month detail
    print(f"  {'Month':<12} {'Actual':>10} {'Predicted':>12} {'Error':>10} {'Error %':>9}")
    print("  " + "─" * 56)
    for _, row in test_df.iterrows():
        pred_row = forecast[forecast["ds"] == row["ds"]].iloc[0]
        pred_val = max(pred_row["yhat"], 0)
        err      = pred_val - row["generation"]
        err_pct  = (err / row["generation"] * 100) if row["generation"] != 0 else 0
        label    = row["ds"].strftime("%b %Y")
        print(
            f"  {label:<12} {row['generation']:>8.1f}   "
            f"{pred_val:>10.1f}   {err:>+8.1f}   {err_pct:>+7.1f}%"
        )


if __name__ == "__main__":
    evaluate()
