"""
Shared fixtures.

Every test runs against the synthetic CSVs in backend/sample_data and a
throwaway models folder, so the suite never reads the private inverter data
or overwrites a real trained model.
"""

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from settings import get_settings

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Point the app at sample data and an empty, per-test models folder."""
    monkeypatch.setenv("SOLARCAST_DATA_DIR", str(SAMPLE_DATA_DIR))
    monkeypatch.setenv("SOLARCAST_MODELS_DIR", str(tmp_path / "models"))
    monkeypatch.delenv("SOLARCAST_RATE_PER_UNIT", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def trained_models_dir(tmp_path_factory):
    """Train once per test session; tests copy the result instead of retraining."""
    from model.train import train

    models_dir = tmp_path_factory.mktemp("trained-models")
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SOLARCAST_DATA_DIR", str(SAMPLE_DATA_DIR))
        mp.setenv("SOLARCAST_MODELS_DIR", str(models_dir))
        get_settings.cache_clear()
        train()
    get_settings.cache_clear()
    return models_dir


@pytest.fixture
def trained(trained_models_dir):
    """A models folder that already contains a trained model."""
    target = get_settings().models_dir
    shutil.copytree(trained_models_dir, target)
    return target


@pytest.fixture
def client():
    from api.main import app
    from api.model_store import model_store

    model_store.reset()
    with TestClient(app) as test_client:
        yield test_client
    model_store.reset()
