import json
from datetime import date
from pathlib import Path

from scripts.export_demo_data import export_demo_data
from scripts.generate_sample_data import build_rows, write_csv_files
from settings import get_settings

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"


def test_generator_reproduces_the_committed_sample_files(tmp_path):
    write_csv_files(build_rows(), tmp_path)

    for committed in sorted(SAMPLE_DATA_DIR.glob("*-summary.csv")):
        assert (tmp_path / committed.name).read_text() == committed.read_text()
    assert len(list(tmp_path.iterdir())) == 3


def test_extending_the_end_month_only_appends_rows():
    base = build_rows()
    extended = build_rows(end=(2026, 9))

    assert len(extended) == len(base) + 9
    # Every earlier month is unchanged, apart from the "latest month" marker.
    assert [r["generation"] for r in extended[: len(base)]] == [r["generation"] for r in base]
    assert extended[-1]["received"] == "" and base[-1]["received"] == ""
    assert extended[len(base) - 1]["received"] != ""


def test_export_writes_the_three_files_the_dashboard_reads(tmp_path):
    paths = export_demo_data(tmp_path / "demo", today=date(2026, 10, 3))

    assert sorted(p.name for p in paths) == ["history.json", "predictions.json", "status.json"]

    history = json.loads((tmp_path / "demo" / "history.json").read_text())
    assert [y["year"] for y in history["years"]] == [2023, 2024, 2025, 2026]
    assert history["years"][-1]["rows"][-1]["period"] == "Sep 2026"   # up to last month

    predictions = json.loads((tmp_path / "demo" / "predictions.json").read_text())
    months = [p["month"] for p in predictions["predictions"]]
    assert predictions["modelTrained"] is True
    assert len(months) == 12 and months[0] == "Oct 2026" and months[-1] == "Sep 2027"
    assert set(predictions["predictions"][0]) == {"month", "generation", "creditableExport", "cash"}
    assert set(predictions["predictions"][0]["cash"]) == {"value", "lower", "upper"}

    status = json.loads((tmp_path / "demo" / "status.json").read_text())
    assert status["modelTrained"] is True and status["lastTrainedAt"]


def test_export_never_reads_the_configured_data_folder(tmp_path, monkeypatch):
    # A folder standing in for private data: one file that would break loading
    # if the export ever looked at it.
    private = tmp_path / "private"
    private.mkdir()
    (private / "2026-summary.csv").write_text("not,the,right,shape\n1,2,3,4\n")
    monkeypatch.setenv("SOLARCAST_DATA_DIR", str(private))
    get_settings.cache_clear()

    export_demo_data(tmp_path / "demo", today=date(2026, 10, 3))

    history = json.loads((tmp_path / "demo" / "history.json").read_text())
    assert len(history["years"]) == 4
    # The caller's settings are restored afterwards.
    assert get_settings().data_dir == private
    assert not (tmp_path / "models").exists()   # the per-test models folder was not touched
