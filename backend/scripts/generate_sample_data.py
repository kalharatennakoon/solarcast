"""
generate_sample_data.py
-----------------------
Writes a small, entirely synthetic dataset to backend/sample_data/ in the same
CSV layout as the real yearly summaries. It exists so the test suite, CI and
anyone cloning the repo can run SolarCast without the private inverter data.

The numbers come from a sine-wave season plus random noise with a fixed seed.
They are not derived from any real solar system.

The committed files cover 2023–2025 and never change. The public demo site
uses the same generator with a later end month (see export_demo_data.py), so
its history always runs up to last month.

Usage (from backend/):
    python scripts/generate_sample_data.py
"""

import calendar
import csv
import math
from pathlib import Path

import numpy as np

OUT_DIR = Path(__file__).resolve().parent.parent / "sample_data"
START_YEAR = 2023
DEFAULT_END = (2025, 12)   # (year, month) of the last row in the committed files
RATE_PER_UNIT = 37

HEADER = [
    "Year", "Month", "Total Generation (kWh)", "Total Export to CEB (kWh)",
    "Total Import from CEB (kWh)", "Creditable Export (kWh)", "Total Cash (LKR)",
    "Cash Received (LKR)", "Merge Group", "Exclude From Training", "Notes",
]


def _month_row(rng: np.random.Generator, year: int, month: int) -> dict:
    season = 90 * math.cos(2 * math.pi * (month - 3) / 12)   # peak around March
    generation = round(580 + season + rng.normal(0, 25))
    export = round(generation * rng.uniform(0.80, 0.95))
    imported = round(rng.uniform(50, 70))
    creditable = export - imported
    cash = creditable * RATE_PER_UNIT
    return {
        "year": year, "month": calendar.month_name[month],
        "generation": generation, "export": export, "import": imported,
        "creditable": creditable, "cash": cash, "received": cash,
        "merge": "", "exclude": "", "notes": "",
    }


def build_rows(end: tuple[int, int] = DEFAULT_END) -> list[dict]:
    """
    One row per month from January 2023 to `end` (year, month), inclusive.

    The random generator is seeded and months are drawn in order, so extending
    `end` only appends rows; every earlier month keeps exactly the same values.
    """
    end_year, end_month = end
    rng = np.random.default_rng(42)
    rows = [
        _month_row(rng, y, m)
        for y in range(START_YEAR, end_year + 1)
        for m in range(1, 13)
        if (y, m) <= (end_year, end_month)
    ]
    by_key = {(r["year"], r["month"]): r for r in rows}

    # A partial first month, excluded from training.
    first = by_key[(2023, "January")]
    first.update(generation=90, exclude="YES", notes="Partial month; excluded from training")

    # One meter reading that covered two months, split 50/50 between them.
    a, b = by_key[(2024, "January")], by_key[(2024, "February")]
    for field in ("export", "import", "creditable", "cash", "received"):
        shared = (a[field] + b[field]) / 2
        a[field] = b[field] = shared
    for r in (a, b):
        r.update(merge="Jan-Feb", exclude="NO", notes="One reading for both months; split equally")

    # The latest month's payment has not arrived yet.
    rows[-1].update(received="", notes="Cash not yet received")
    return rows


def write_csv_files(rows: list[dict], out_dir: Path) -> list[Path]:
    """Write one <year>-summary.csv per year and return the paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for year in sorted({r["year"] for r in rows}):
        path = out_dir / f"{year}-summary.csv"
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
            for r in (r for r in rows if r["year"] == year):
                money = [f"{r[k]:.2f}" if r[k] != "" else "" for k in ("cash", "received")]
                writer.writerow([
                    r["year"], r["month"], r["generation"], f"{r['export']:g}",
                    f"{r['import']:g}", f"{r['creditable']:g}", *money,
                    r["merge"], r["exclude"], r["notes"],
                ])
        paths.append(path)
    return paths


def main() -> None:
    for path in write_csv_files(build_rows(), OUT_DIR):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
