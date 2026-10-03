import pytest

from api.routes import train as train_route
from model import artefacts
from settings import get_settings

# ── Health ────────────────────────────────────────────────────────────────────


def test_healthz_is_always_ok(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz_is_ready_without_a_model(client):
    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "modelLoaded": False, "detail": None}


def test_readyz_fails_when_the_data_folder_is_missing(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SOLARCAST_DATA_DIR", str(tmp_path / "not-mounted"))
    get_settings.cache_clear()

    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"


# ── Status and predictions ────────────────────────────────────────────────────


def test_untrained_app_reports_no_model_instead_of_failing(client):
    assert client.get("/status").json() == {"modelTrained": False, "lastTrainedAt": None}
    assert client.get("/predict").json() == {"modelTrained": False, "predictions": []}


def test_predict_returns_the_requested_number_of_months(trained, client):
    body = client.get("/predict", params={"months": 3}).json()

    assert body["modelTrained"] is True
    assert len(body["predictions"]) == 3
    assert set(body["predictions"][0]) == {"month", "generation", "creditableExport", "cash"}


@pytest.mark.parametrize("months", ["0", "-1", "13", "500", "abc"])
def test_predict_rejects_out_of_range_months(trained, client, months):
    response = client.get("/predict", params={"months": months})

    assert response.status_code == 422


def test_status_reports_the_last_training_time(trained, client):
    body = client.get("/status").json()

    assert body["modelTrained"] is True
    assert body["lastTrainedAt"] == artefacts.read_trained_at()


def test_unreadable_model_is_reported_as_untrained(trained, client):
    artefacts.model_path().write_bytes(b"this is not a model")

    assert client.get("/status").json()["modelTrained"] is False
    assert client.get("/predict").json() == {"modelTrained": False, "predictions": []}
    assert client.get("/readyz").json()["detail"]


# ── Training ──────────────────────────────────────────────────────────────────


def test_train_then_predict_end_to_end(client):
    trained = client.post("/train")

    assert trained.status_code == 200
    body = trained.json()
    assert body["status"] == "success"
    assert (body["trainingRecords"], body["testRecords"]) == (24, 11)
    assert body["trainPeriod"] == "Feb 2023 → Jan 2025"
    assert body["lastTrainedAt"]

    # The freshly trained model is served without a restart.
    assert client.get("/status").json()["modelTrained"] is True
    assert len(client.get("/predict", params={"months": 12}).json()["predictions"]) == 12


def test_second_training_run_is_rejected_while_one_is_in_progress(client):
    assert train_route._training_lock.acquire(blocking=False)
    try:
        response = client.post("/train")
    finally:
        train_route._training_lock.release()

    assert response.status_code == 409
    assert not artefacts.model_exists()


def test_training_failure_returns_the_reason_and_releases_the_lock(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SOLARCAST_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    response = client.post("/train")

    assert response.status_code == 500
    assert "No CSV files found" in response.json()["detail"]
    assert not train_route._training_lock.locked()


# ── History ───────────────────────────────────────────────────────────────────


def test_history_is_grouped_by_year_with_blanks_as_null(client):
    years = client.get("/history").json()["years"]

    assert [y["year"] for y in years] == [2023, 2024, 2025]
    assert all(len(y["rows"]) == 12 for y in years)

    first, last = years[0]["rows"][0], years[-1]["rows"][-1]
    assert first["excludeTraining"] is True
    assert last["period"] == "Dec 2025"
    assert last["cashReceived"] is None
    assert years[1]["rows"][0]["mergeGroup"] == "Jan-Feb"


def test_history_reports_a_missing_data_folder(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SOLARCAST_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    response = client.get("/history")

    assert response.status_code == 500
    assert "No CSV files found" in response.json()["detail"]


# ── Metrics and CORS ──────────────────────────────────────────────────────────


def test_metrics_endpoint_exposes_request_and_model_metrics(trained, client):
    client.get("/predict", params={"months": 3})
    client.get("/no-such-page")

    text = client.get("/metrics").text

    assert 'solarcast_http_requests_total{method="GET",path="/predict",status="200"}' in text
    assert 'path="unmatched",status="404"' in text
    assert "solarcast_model_loaded 1.0" in text
    assert "solarcast_predicted_months_total" in text
    assert 'path="/metrics"' not in text


def test_cors_allows_only_configured_origins(client):
    allowed = client.get("/status", headers={"Origin": "http://localhost:5173"})
    blocked = client.get("/status", headers={"Origin": "https://example.com"})

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in blocked.headers
