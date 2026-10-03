"""
settings.py
-----------
Runtime configuration for SolarCast, read from environment variables so the
same code runs unchanged on a laptop, in Docker and on Kubernetes.

Variable                    Default                         Purpose
--------------------------  ------------------------------  ---------------------------
SOLARCAST_DATA_DIR          backend/data                    Folder of *-summary.csv files
SOLARCAST_MODELS_DIR        backend/model/saved_models      Where trained artefacts live
SOLARCAST_CORS_ORIGINS      http://localhost:5173, ...      Comma-separated allowed origins
SOLARCAST_RATE_PER_UNIT     37                              LKR paid per creditable kWh
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    models_dir: Path
    cors_origins: tuple[str, ...]
    rate_per_unit: float


@lru_cache
def get_settings() -> Settings:
    """Read settings once per process. Tests call `get_settings.cache_clear()`."""
    return Settings(
        data_dir=Path(os.getenv("SOLARCAST_DATA_DIR") or BACKEND_DIR / "data"),
        models_dir=Path(
            os.getenv("SOLARCAST_MODELS_DIR") or BACKEND_DIR / "model" / "saved_models"
        ),
        cors_origins=_split_csv(
            os.getenv("SOLARCAST_CORS_ORIGINS") or DEFAULT_CORS_ORIGINS
        ),
        rate_per_unit=float(os.getenv("SOLARCAST_RATE_PER_UNIT") or 37),
    )
