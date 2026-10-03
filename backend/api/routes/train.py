import logging
import threading
import time

from fastapi import APIRouter, HTTPException

from api.metrics import TRAINING_DURATION, TRAINING_RUNS
from api.model_store import model_store
from api.schemas import TrainResponse

router = APIRouter()
logger = logging.getLogger("solarcast.train")

# Only one training run at a time: two runs would race to write the same files.
_training_lock = threading.Lock()


@router.post("/train", response_model=TrainResponse)
def post_train():
    """
    Trains the Prophet model on the historical CSV data.
    Uses a 70/30 chronological split (training data precedes test data).
    Saves the trained model and seasonal ratio tables to the models folder.
    Returns 409 if a training run is already in progress.
    """
    if not _training_lock.acquire(blocking=False):
        TRAINING_RUNS.labels("rejected").inc()
        raise HTTPException(status_code=409, detail="Training is already in progress.")

    try:
        from model.train import train

        started = time.perf_counter()
        summary = train()
        TRAINING_DURATION.observe(time.perf_counter() - started)
        TRAINING_RUNS.labels("success").inc()

        # Pick up the new model immediately rather than on the next request.
        model_store.get()

        return TrainResponse(
            status="success",
            trainingRecords=summary.training_records,
            testRecords=summary.test_records,
            trainPeriod=summary.train_period,
            testPeriod=summary.test_period,
            lastTrainedAt=summary.trained_at,
        )

    except Exception as e:
        TRAINING_RUNS.labels("failure").inc()
        logger.exception("Training failed")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}") from e

    finally:
        _training_lock.release()
