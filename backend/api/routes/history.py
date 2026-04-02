import calendar
import math
from fastapi import APIRouter, HTTPException

from model.preprocess import load_raw
from api.schemas import HistoryResponse, YearGroup, HistoryRow

router = APIRouter()


def _clean(value):
    """Convert NaN / float('inf') to None for JSON serialisation."""
    if value is None:
        return None
    try:
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except TypeError:
        return value


@router.get("/history", response_model=HistoryResponse)
def get_history():
    """
    Returns all historical solar records grouped by year.
    Merged month pairs show the 50/50 split CEB values already stored in the
    CSV — each month has its own row with equal share of the combined reading.
    """
    try:
        raw = load_raw()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    year_map: dict[int, list[HistoryRow]] = {}

    for _, row in raw.iterrows():
        year      = int(row["year"])
        month     = str(row["month"]).strip()
        month_num = int(row["month_num"])
        period    = f"{calendar.month_abbr[month_num]} {year}"

        merge_group = row["merge_group"] if row["merge_group"] != "" else None
        note_val    = row.get("notes", None)
        note        = str(note_val).strip() if note_val and str(note_val) != "nan" else None

        record = HistoryRow(
            period=period,
            month=month,
            year=year,
            generation=_clean(row["generation"]),
            export=_clean(row["export"]),
            importKwh=_clean(row["import_kwh"]),
            creditableExport=_clean(row["creditable_export"]),
            totalCash=_clean(row["total_cash"]),
            cashReceived=_clean(row["cash_received"]),
            mergeGroup=merge_group,
            excludeTraining=bool(row["exclude_training"]),
            note=note,
        )

        year_map.setdefault(year, []).append(record)

    years = [
        YearGroup(year=yr, rows=rows)
        for yr, rows in sorted(year_map.items())
    ]

    return HistoryResponse(years=years)
