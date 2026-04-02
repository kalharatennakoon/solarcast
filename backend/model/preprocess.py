"""
preprocess.py
-------------
Loads all yearly CSV files, applies business rules for exclusions, engineers
features, and returns a clean DataFrame ready for model training.

Business rules applied:
  - Feb+Mar 2024: Both rows marked Exclude From Training = YES in the CSV.
    Skipped entirely — Feb was a partial month (26–29 Feb) and the pair's CEB
    values cannot be cleanly separated.
  - All other merged pairs (Apr+May 2024, Jan+Feb 2025, Jan+Feb 2026): Each
    month already has its own row in the CSV with the 50/50 split CEB values
    applied at source. Both rows are included as separate training records.
  - Rows with no creditable_export are dropped (incomplete CEB reading).
"""

import calendar
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"

MONTH_ORDER = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

NUMERIC_COLS = [
    "generation", "export", "import_kwh",
    "creditable_export", "total_cash", "cash_received",
]


def load_raw() -> pd.DataFrame:
    """Concatenate all *-summary.csv files into one raw DataFrame."""
    frames = []
    for path in sorted(DATA_DIR.glob("*-summary.csv")):
        df = pd.read_csv(path, dtype=str)
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")
    raw = pd.concat(frames, ignore_index=True)

    raw.columns = [
        "year", "month", "generation", "export", "import_kwh",
        "creditable_export", "total_cash", "cash_received",
        "merge_group", "exclude_training", "notes",
    ]

    for col in NUMERIC_COLS:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")

    raw["year"] = pd.to_numeric(raw["year"], errors="coerce").ffill().astype(int)
    raw["month"] = raw["month"].str.strip()
    raw["month_num"] = raw["month"].map(MONTH_ORDER)
    raw["merge_group"] = raw["merge_group"].fillna("").str.strip()
    raw["exclude_training"] = raw["exclude_training"].fillna("").str.upper().eq("YES")

    raw["ds"] = pd.to_datetime(
        dict(year=raw["year"], month=raw["month_num"], day=1)
    )
    raw["days_in_month"] = raw.apply(
        lambda r: calendar.monthrange(int(r["year"]), int(r["month_num"]))[1], axis=1
    )
    return raw


def preprocess(exclude_incomplete: bool = True) -> pd.DataFrame:
    """
    Return a clean, training-ready DataFrame.

    Parameters
    ----------
    exclude_incomplete : bool
        If True (default), drop records that have no creditable_export value.

    Returns
    -------
    pd.DataFrame with columns:
        ds, year, month, month_num, days_in_month,
        generation, export, import_kwh, creditable_export,
        cash_received, total_cash, is_merged,
        year_index, sin_month, cos_month
    """
    raw = load_raw()

    # Drop rows marked excluded from training
    df = raw[~raw["exclude_training"]].copy()

    # Build records — each row in the CSV becomes one training record
    records = [_make_record(row) for _, row in df.iterrows()]
    df = pd.DataFrame(records).sort_values("ds").reset_index(drop=True)

    if exclude_incomplete:
        df = df.dropna(subset=["creditable_export"]).reset_index(drop=True)

    # ── Feature engineering ───────────────────────────────────────────────
    df["year_index"] = df["year"] - df["year"].min()
    df["sin_month"] = np.sin(2 * np.pi * df["month_num"] / 12)
    df["cos_month"] = np.cos(2 * np.pi * df["month_num"] / 12)

    return df


def _make_record(row: pd.Series) -> dict:
    return {
        "ds": row["ds"],
        "year": int(row["year"]),
        "month": row["month"],
        "month_num": int(row["month_num"]),
        "days_in_month": int(row["days_in_month"]),
        "generation": row["generation"],
        "export": row["export"],
        "import_kwh": row["import_kwh"],
        "creditable_export": row["creditable_export"],
        "cash_received": row["cash_received"],
        "total_cash": row["total_cash"],
        "is_merged": row["merge_group"] != "",
    }


def train_test_split(df: pd.DataFrame, train_ratio: float = 0.70):
    """
    Chronological split — training data comes before test data.
    Never shuffle time-series data.
    """
    split_idx = int(len(df) * train_ratio)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


if __name__ == "__main__":
    df = preprocess()
    train, test = train_test_split(df)
    print(f"Clean records : {len(df)}")
    print(f"Training set  : {len(train)}  ({train['ds'].min().strftime('%b %Y')} → {train['ds'].max().strftime('%b %Y')})")
    print(f"Test set      : {len(test)}   ({test['ds'].min().strftime('%b %Y')} → {test['ds'].max().strftime('%b %Y')})")
    print(df[["ds", "generation", "creditable_export", "cash_received", "is_merged"]].to_string())
