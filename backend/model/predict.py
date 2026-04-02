"""
predict.py
----------
Loads the trained Prophet model and seasonal ratio tables, then produces
predictions for the next N months with confidence intervals.

Prediction pipeline
-------------------
Step 1  Prophet predicts generation (kWh) for the target month.
        Outputs: yhat (point estimate), yhat_lower, yhat_upper (90% CI).

Step 2  Derive export from generation using the historical seasonal ratio:
          export = generation × export_ratio[month]
        Confidence bounds use ±1.5 × std of the ratio.

Step 3  Derive import using the historical monthly average:
          import = import_avg[month]

Step 4  Creditable export:
          creditable_export = export − import

Step 5  Total cash (LKR):
          cash = creditable_export × 37

Confidence propagation
----------------------
  generation_lo / hi  → from Prophet yhat_lower / yhat_upper
  export_lo           = generation_lo × (ratio_mean − 1.5 × ratio_std)
  export_hi           = generation_hi × (ratio_mean + 1.5 × ratio_std)
  creditable_lo       = export_lo − import_mean
  creditable_hi       = export_hi − import_mean
  cash_lo             = creditable_lo × 37
  cash_hi             = creditable_hi × 37
"""

import json
from datetime import date
from pathlib import Path

import joblib
import pandas as pd

MODELS_DIR = Path(__file__).parent / "saved_models"
RATE_PER_UNIT = 37  # LKR per kWh


def load_artefacts():
    model = joblib.load(MODELS_DIR / "prophet_generation.pkl")
    with open(MODELS_DIR / "seasonal_ratios.json") as f:
        ratios = {int(k): v for k, v in json.load(f).items()}
    return model, ratios


def predict(months: int = 1, start_date: date = None) -> list[dict]:
    """
    Predict solar generation and derived metrics for the next `months` months.

    Parameters
    ----------
    months : int
        Number of future months to predict (1, 3, 6, or 12).
    start_date : date, optional
        First month to predict. Defaults to the first day of next month
        relative to today.

    Returns
    -------
    List of dicts, one per predicted month:
        {
            "month"             : "Apr 2026",
            "generation"        : {"value": 650, "lower": 585, "upper": 715},
            "creditable_export" : {"value": 555, "lower": 495, "upper": 615},
            "cash"              : {"value": 20535.00, "lower": 18315.00, "upper": 22755.00},
        }
    """
    model, ratios = load_artefacts()

    if start_date is None:
        today = date.today()
        # First day of next month
        if today.month == 12:
            start_date = date(today.year + 1, 1, 1)
        else:
            start_date = date(today.year, today.month + 1, 1)

    # Build future DataFrame for Prophet (needs 'ds' column)
    future_dates = pd.date_range(start=start_date, periods=months, freq="MS")
    future_df = pd.DataFrame({"ds": future_dates})

    forecast = model.predict(future_df)

    results = []
    for _, row in forecast.iterrows():
        month_num = row["ds"].month
        label = row["ds"].strftime("%b %Y")
        r = ratios[month_num]

        gen_val = max(row["yhat"], 0)
        gen_lo  = max(row["yhat_lower"], 0)
        gen_hi  = max(row["yhat_upper"], 0)

        ratio_mean = r["export_ratio_mean"]
        ratio_std  = r["export_ratio_std"] if r["n"] > 1 else ratio_mean * 0.10

        export_val = gen_val * ratio_mean
        export_lo  = gen_lo  * max(ratio_mean - 1.5 * ratio_std, 0)
        export_hi  = gen_hi  * (ratio_mean + 1.5 * ratio_std)

        import_val = r["import_mean"]

        cred_val = max(export_val - import_val, 0)
        cred_lo  = max(export_lo  - import_val, 0)
        cred_hi  = max(export_hi  - import_val, 0)

        cash_val = round(cred_val * RATE_PER_UNIT, 2)
        cash_lo  = round(cred_lo  * RATE_PER_UNIT, 2)
        cash_hi  = round(cred_hi  * RATE_PER_UNIT, 2)

        results.append({
            "month": label,
            "generation": {
                "value": round(gen_val, 1),
                "lower": round(gen_lo, 1),
                "upper": round(gen_hi, 1),
            },
            "creditable_export": {
                "value": round(cred_val, 1),
                "lower": round(cred_lo, 1),
                "upper": round(cred_hi, 1),
            },
            "cash": {
                "value": cash_val,
                "lower": cash_lo,
                "upper": cash_hi,
            },
        })

    return results


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    preds = predict(months=n)
    for p in preds:
        g = p["generation"]
        c = p["cash"]
        print(
            f"{p['month']:10s}  "
            f"Generation: {g['value']:6.1f} kWh  [{g['lower']:6.1f} – {g['upper']:6.1f}]  |  "
            f"Cash: LKR {c['value']:,.2f}  [{c['lower']:,.2f} – {c['upper']:,.2f}]"
        )
