import pandas as pd
import pytest

from model.preprocess import load_raw, preprocess, train_test_split
from settings import get_settings


def test_load_raw_reads_every_yearly_file():
    raw = load_raw()

    assert len(raw) == 36
    assert sorted(raw["year"].unique()) == [2023, 2024, 2025]
    assert raw["ds"].is_monotonic_increasing


def test_rows_marked_exclude_are_dropped():
    raw = load_raw()
    df = preprocess()

    assert raw["exclude_training"].sum() == 1
    assert len(df) == 35
    assert df["ds"].min() == pd.Timestamp("2023-02-01")


def test_merged_months_stay_as_separate_flagged_records():
    df = preprocess()
    merged = df[df["is_merged"]]

    assert list(merged["month"]) == ["January", "February"]
    assert merged["export"].nunique() == 1          # 50/50 split of one reading
    assert merged["generation"].nunique() == 2      # generation is per month


def test_split_is_chronological_and_never_shuffled():
    df = preprocess()
    train, test = train_test_split(df, train_ratio=0.70)

    assert len(train) == 24 and len(test) == 11
    assert train["ds"].max() < test["ds"].min()


def test_missing_data_folder_gives_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setenv("SOLARCAST_DATA_DIR", str(tmp_path / "nowhere"))
    get_settings.cache_clear()

    with pytest.raises(FileNotFoundError, match="No CSV files found"):
        load_raw()


def test_csv_with_wrong_column_count_is_rejected(tmp_path, monkeypatch):
    (tmp_path / "2030-summary.csv").write_text("Year,Month\n2030,January\n")
    monkeypatch.setenv("SOLARCAST_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="expected 11 columns, found 2"):
        load_raw()
