"""
Health endpoints for container orchestrators.

  /healthz  liveness  — the process is up and able to answer.
  /readyz   readiness — the app can do useful work (its data folder is mounted).

A missing model does not make the app "not ready": it still serves history and
can be trained through POST /train.
"""

from fastapi import APIRouter, Response, status

from api.model_store import model_store
from api.schemas import HealthResponse
from settings import get_settings

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse, response_model_exclude_none=True)
def healthz():
    return HealthResponse(status="ok")


@router.get("/readyz", response_model=HealthResponse)
def readyz(response: Response):
    data_dir = get_settings().data_dir
    model_loaded = model_store.get() is not None

    if not data_dir.is_dir():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="unavailable",
            modelLoaded=model_loaded,
            detail=f"Data folder not found: {data_dir}",
        )

    return HealthResponse(
        status="ready",
        modelLoaded=model_loaded,
        detail=model_store.load_error,
    )
