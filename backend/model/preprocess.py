"""
preprocess.py
-------------
Loads all yearly CSV files, applies business rules for merged months and
exclusions, engineers features, and returns a clean DataFrame ready for
model training.

Business rules applied:
  - Feb 2024 (26-29 Feb, partial month) → excluded from training entirely.
    The Feb-Mar 2024 merged pair is excluded as a whole because one half is
    invalid. Mar 2024 generation cannot be paired with clean CEB values.
  - All other merged month pairs → split into two separate records.
    Each month keeps its own real generation value (already recorded individually).
    CEB values (export, import, creditable export, cash) are divided equally
    between the two months (50/50 split) since the combined reading cannot be
    attributed to either month individually.
    This gives each month its own training record and prevents months like
    February from having zero training data.
  - Rows with no CEB data and no creditable export are dropped (can't train
    the full prediction pipeline without them).
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
        If True (default), drop records that have no creditable_export value
        (cannot train the full cash-prediction pipeline without it).

    Returns
    -------
    pd.DataFrame with columns:
        ds, year, month, month_num, days_in_month,
        generation, export, import_kwh, creditable_export,
        cash_received, total_cash,
        is_merged, year_index, sin_month, cos_month
    """
    raw = load_raw()
    records = []
    processed_groups: set = set()

    for _, row in raw.iterrows():
        group = row["merge_group"]
        excluded = row["exclude_training"]

        # ── Standalone month ──────────────────────────────────────────────
        if group == "":
            if excluded:
                continue
            records.append(_make_record(row, is_merged=False))
            continue

        # ── Merged group ──────────────────────────────────────────────────
        if group in processed_groups:
            continue
        processed_groups.add(group)

        group_rows = raw[raw["merge_group"] == group]

        # If any row in the pair is marked excluded (e.g. Feb 2024 partial),
        # discard the entire merged pair — CEB values are entangled.
        if group_rows["exclude_training"].any():
            continue

        # Split the merged pair into two separate records.
        # Each month keeps its own generation.
        # CEB values (export, import, creditable export, cash) are divided
        # equally (50/50) between the two months.
        anchor = group_rows[group_rows["export"].notna()].iloc[0]
        n = len(group_rows)

        for _, month_row in group_rows.iterrows():
            split_row = month_row.copy()
            split_row["export"]           = anchor["export"] / n
            split_row["import_kwh"]       = anchor["import_kwh"] / n
            split_row["creditable_export"] = anchor["creditable_export"] / n
            split_row["cash_received"] = (
                anchor["cash_received"] / n
                if pd.notna(anchor["cash_received"]) else np.nan
            )
            split_row["total_cash"] = (
                anchor["total_cash"] / n
                if pd.notna(anchor["total_cash"]) else np.nan
            )
            records.append(_make_record(split_row, is_merged=True))

    df = pd.DataFrame(records).sort_values("ds").reset_index(drop=True)

    if exclude_incomplete:
        df = df.dropna(subset=["creditable_export"]).reset_index(drop=True)

    # ── Feature engineering ───────────────────────────────────────────────
    df["year_index"] = df["year"] - df["year"].min()
    df["sin_month"] = np.sin(2 * np.pi * df["month_num"] / 12)
    df["cos_month"] = np.cos(2 * np.pi * df["month_num"] / 12)

    return df


def _make_record(row: pd.Series, is_merged: bool) -> dict:
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
        "is_merged": is_merged,
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
