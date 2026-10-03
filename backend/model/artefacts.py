"""
artefacts.py
------------
Single place that knows where trained artefacts live and how they are read
and written. Every write goes to a temporary file first and is then renamed
into place, so a request that arrives mid-training never reads a half-written
model.
"""

import json
import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from settings import get_settings

MODEL_FILE = "prophet_generation.pkl"
RATIOS_FILE = "seasonal_ratios.json"
TEST_SET_FILE = "test_set.csv"
TRAINED_AT_FILE = "trained_at.txt"

TRAINED_AT_FORMAT = "%b %d, %Y, %I:%M:%S %p"


def models_dir() -> Path:
    return get_settings().models_dir


def model_path() -> Path:
    return models_dir() / MODEL_FILE


def ratios_path() -> Path:
    return models_dir() / RATIOS_FILE


def test_set_path() -> Path:
    return models_dir() / TEST_SET_FILE


def trained_at_path() -> Path:
    return models_dir() / TRAINED_AT_FILE


def model_exists() -> bool:
    return model_path().exists() and ratios_path().exists()


def _atomic_write(path: Path, write: Callable[[Path], None]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    write(tmp)
    os.replace(tmp, path)


# ── Read ──────────────────────────────────────────────────────────────────────


def load_artefacts() -> tuple[object, dict[int, dict]]:
    """Return (prophet_model, seasonal_ratios keyed by calendar month 1–12)."""
    model = joblib.load(model_path())
    with open(ratios_path()) as f:
        ratios = {int(k): v for k, v in json.load(f).items()}
    return model, ratios


def load_test_set() -> pd.DataFrame:
    return pd.read_csv(test_set_path(), parse_dates=["ds"])


def read_trained_at() -> str | None:
    """Most recent training timestamp (the file is newest-first)."""
    path = trained_at_path()
    if not path.exists():
        return None
    lines = path.read_text().splitlines()
    return (lines[0].strip() or None) if lines else None


# ── Write ─────────────────────────────────────────────────────────────────────


def save_artefacts(model, ratios: dict, test_df: pd.DataFrame) -> str:
    """
    Persist one training run and return its timestamp.

    The model file is written last: the API reloads when that file changes,
    so by then the matching ratio table is already in place.
    """
    _atomic_write(
        ratios_path(), lambda p: p.write_text(json.dumps(ratios, indent=2))
    )
    _atomic_write(test_set_path(), lambda p: test_df.to_csv(p, index=False))

    trained_at = datetime.now().strftime(TRAINED_AT_FORMAT)
    ts_path = trained_at_path()
    history = ts_path.read_text().strip() if ts_path.exists() else ""
    entries = [trained_at] + ([history] if history else [])
    _atomic_write(ts_path, lambda p: p.write_text("\n".join(entries)))

    _atomic_write(model_path(), lambda p: joblib.dump(model, p))
    return trained_at
