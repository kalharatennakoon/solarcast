from typing import Optional
from pydantic import BaseModel


# ── History ───────────────────────────────────────────────────────────────────

class HistoryRow(BaseModel):
    period: str
    month: str
    year: int
    generation: Optional[float]
    export: Optional[float]
    importKwh: Optional[float]
    creditableExport: Optional[float]
    totalCash: Optional[float]
    cashReceived: Optional[float]
    mergeGroup: Optional[str]
    excludeTraining: bool
    note: Optional[str]


class YearGroup(BaseModel):
    year: int
    rows: list[HistoryRow]


class HistoryResponse(BaseModel):
    years: list[YearGroup]


# ── Predictions ───────────────────────────────────────────────────────────────

class Interval(BaseModel):
    value: float
    lower: float
    upper: float


class PredictionMonth(BaseModel):
    month: str
    generation: Interval
    creditableExport: Interval
    cash: Interval


class PredictResponse(BaseModel):
    modelTrained: bool
    predictions: list[PredictionMonth]


# ── Training ──────────────────────────────────────────────────────────────────

class TrainResponse(BaseModel):
    status: str
    trainingRecords: int
    testRecords: int
    trainPeriod: str
    testPeriod: str
    lastTrainedAt: Optional[str]


# ── Status ────────────────────────────────────────────────────────────────────

class StatusResponse(BaseModel):
    modelTrained: bool
    lastTrainedAt: Optional[str]
