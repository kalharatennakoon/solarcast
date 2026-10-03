from fastapi import APIRouter, Query

from api.metrics import PREDICTED_MONTHS
from api.model_store import model_store
from api.schemas import Interval, PredictionMonth, PredictResponse, StatusResponse
from model.artefacts import read_trained_at
from model.predict import predict as run_predict

router = APIRouter()

MAX_MONTHS = 12


@router.get("/predict", response_model=PredictResponse)
def get_predictions(months: int = Query(default=1, ge=1, le=MAX_MONTHS)):
    """
    Returns predictions for the next N months (1 to 12).
    Returns modelTrained: false with an empty list if the model has
    not been trained yet — run POST /train first.
    """
    artefacts = model_store.get()
    if artefacts is None:
        return PredictResponse(modelTrained=False, predictions=[])

    raw = run_predict(months=months, artefacts=artefacts)
    PREDICTED_MONTHS.inc(len(raw))

    predictions = [
        PredictionMonth(
            month=p["month"],
            generation=Interval(**p["generation"]),
            creditableExport=Interval(**p["creditable_export"]),
            cash=Interval(**p["cash"]),
        )
        for p in raw
    ]

    return PredictResponse(modelTrained=True, predictions=predictions)


@router.get("/status", response_model=StatusResponse)
def get_status():
    """Returns whether the model has been trained and when it was last trained."""
    trained = model_store.get() is not None
    return StatusResponse(
        modelTrained=trained,
        lastTrainedAt=read_trained_at() if trained else None,
    )
