from pathlib import Path

from fastapi import APIRouter

from api.schemas import PredictResponse, PredictionMonth, Interval

router = APIRouter()

MODELS_DIR = Path(__file__).parent.parent.parent / "model" / "saved_models"


def _model_trained() -> bool:
    return (MODELS_DIR / "prophet_generation.pkl").exists()


@router.get("/predict", response_model=PredictResponse)
def get_predictions(months: int = 1):
    """
    Returns predictions for the next N months (1, 3, 6, or 12).
    Returns modelTrained: false with an empty list if the model has
    not been trained yet — run POST /train first.
    """
    if not _model_trained():
        return PredictResponse(modelTrained=False, predictions=[])

    from model.predict import predict as run_predict

    raw = run_predict(months=months)

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


@router.get("/status")
def get_status():
    """Returns whether the model has been trained."""
    return {"modelTrained": _model_trained()}
