"""
export_demo_data.py
-------------------
Builds the data behind the public demo site (GitHub Pages).

GitHub Pages can only serve static files, so there is no backend there. This
script runs the real pipeline once, at build time, and saves what the API
would have answered as JSON files the dashboard reads instead:

    history.json       what GET /history returns
    status.json        what GET /status returns
    predictions.json   what GET /predict?months=12 returns

PRIVACY: the demo is public, so this script only ever uses synthetic data. It
generates its own CSVs in a temporary folder and points the pipeline at them.
It deliberately ignores SOLARCAST_DATA_DIR, so real inverter data cannot end
up in the output even if that variable is set.

Usage (from backend/):
    python -m scripts.export_demo_data ../frontend/public/demo
"""

import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

from scripts.generate_sample_data import build_rows, write_csv_files
from settings import get_settings


def _previous_month(today: date) -> tuple[int, int]:
    return (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)


def export_demo_data(out_dir: Path, today: date | None = None) -> list[Path]:
    """Write the demo JSON files to `out_dir` and return their paths."""
    today = today or date.today()

    saved = {k: os.environ.get(k) for k in ("SOLARCAST_DATA_DIR", "SOLARCAST_MODELS_DIR")}
    with tempfile.TemporaryDirectory() as tmp:
        data_dir, models_dir = Path(tmp) / "data", Path(tmp) / "models"

        # History runs up to last month, so the forecast starts where it ends.
        write_csv_files(build_rows(end=_previous_month(today)), data_dir)

        os.environ["SOLARCAST_DATA_DIR"] = str(data_dir)
        os.environ["SOLARCAST_MODELS_DIR"] = str(models_dir)
        get_settings.cache_clear()
        try:
            from api.routes.history import get_history
            from model.artefacts import load_artefacts, read_trained_at
            from model.predict import predict
            from model.train import train

            train()
            start = date(today.year, today.month, 1)
            predictions = predict(months=12, start_date=start, artefacts=load_artefacts())

            payloads = {
                "history.json": get_history().model_dump(mode="json"),
                "status.json": {"modelTrained": True, "lastTrainedAt": read_trained_at()},
                "predictions.json": {
                    "modelTrained": True,
                    "predictions": [
                        {
                            "month": p["month"],
                            "generation": p["generation"],
                            "creditableExport": p["creditable_export"],
                            "cash": p["cash"],
                        }
                        for p in predictions
                    ],
                },
            }
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            get_settings.cache_clear()

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, payload in payloads.items():
        path = out_dir / name
        path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
        paths.append(path)
    return paths


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python -m scripts.export_demo_data <output folder>")
    for path in export_demo_data(Path(sys.argv[1])):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
