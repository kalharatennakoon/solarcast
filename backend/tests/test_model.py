from datetime import date

import pytest

from model import artefacts
from model.evaluate import evaluate
from model.predict import predict
from settings import get_settings


def test_training_writes_all_artefacts_and_no_temp_files(trained):
    names = sorted(p.name for p in trained.iterdir())

    assert names == [
        artefacts.MODEL_FILE,
        artefacts.RATIOS_FILE,
        artefacts.TEST_SET_FILE,
        artefacts.TRAINED_AT_FILE,
    ]
    assert artefacts.model_exists()
    assert artefacts.read_trained_at()


def test_seasonal_ratios_cover_every_calendar_month(trained):
    _, ratios = artefacts.load_artefacts()

    assert sorted(ratios) == list(range(1, 13))
    assert all(0 < r["export_ratio_mean"] <= 1 for r in ratios.values())


def test_predict_returns_one_entry_per_month_in_order(trained):
    results = predict(months=12, start_date=date(2026, 1, 1))

    assert [r["month"] for r in results][:3] == ["Jan 2026", "Feb 2026", "Mar 2026"]
    assert len(results) == 12


def test_predicted_intervals_are_ordered_and_non_negative(trained):
    for result in predict(months=12, start_date=date(2026, 1, 1)):
        for key in ("generation", "creditable_export", "cash"):
            interval = result[key]
            assert 0 <= interval["lower"] <= interval["value"] <= interval["upper"], (
                result["month"], key, interval,
            )


def test_cash_is_creditable_export_times_the_unit_rate(trained):
    rate = get_settings().rate_per_unit
    for result in predict(months=6, start_date=date(2026, 1, 1)):
        expected = result["creditable_export"]["value"] * rate
        # creditable export is rounded to 0.1 kWh before it is reported
        assert result["cash"]["value"] == pytest.approx(expected, abs=rate * 0.05 + 0.01)


def test_unit_rate_comes_from_the_environment(trained, monkeypatch):
    baseline = predict(months=1, start_date=date(2026, 1, 1))[0]["cash"]["value"]

    monkeypatch.setenv("SOLARCAST_RATE_PER_UNIT", "74")
    get_settings.cache_clear()
    doubled = predict(months=1, start_date=date(2026, 1, 1))[0]["cash"]["value"]

    assert doubled == pytest.approx(baseline * 2, abs=0.02)


@pytest.mark.parametrize("months", [0, -1])
def test_predict_rejects_non_positive_months(trained, months):
    with pytest.raises(ValueError, match="at least 1"):
        predict(months=months)


def test_evaluate_reports_metrics_on_the_held_out_months(trained):
    metrics = evaluate()

    assert metrics["records"] == 11
    assert 0 < metrics["mae"] <= metrics["rmse"]
    # The sample data is a clean seasonal curve; a working model fits it well.
    assert metrics["mape"] < 15


def test_retraining_keeps_a_newest_first_timestamp_history(trained):
    from model.train import train

    train()
    lines = artefacts.trained_at_path().read_text().splitlines()

    assert len(lines) == 2
    assert artefacts.read_trained_at() == lines[0]
