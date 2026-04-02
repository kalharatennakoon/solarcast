from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.schemas import TrainResponse

router = APIRouter()

MODELS_DIR = Path(__file__).parent.parent.parent / "model" / "saved_models"


def _read_trained_at() -> str | None:
    path = MODELS_DIR / "trained_at.txt"
    return path.read_text().strip() if path.exists() else None


@router.post("/train", response_model=TrainResponse)
def post_train():
    """
    Trains the Prophet model on the historical CSV data.
    Uses a 70/30 chronological split (training data precedes test data).
    Saves the trained model and seasonal ratio tables to model/saved_models/.
    """
    try:
        from model.preprocess import preprocess, train_test_split
        from model.train import train

        # Preprocess once — reuse the split for both the response and training.
        df = preprocess()
        train_df, test_df = train_test_split(df, train_ratio=0.70)
        train()

        return TrainResponse(
            status="success",
            trainingRecords=len(train_df),
            testRecords=len(test_df),
            trainPeriod=f"{train_df['ds'].min().strftime('%b %Y')} → {train_df['ds'].max().strftime('%b %Y')}",
            testPeriod=f"{test_df['ds'].min().strftime('%b %Y')} → {test_df['ds'].max().strftime('%b %Y')}",
            lastTrainedAt=_read_trained_at(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")
