import sys
from pathlib import Path

# Add backend/ to sys.path so model/ and api/ packages resolve correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import history, predict, train

app = FastAPI(
    title="SolarCast API",
    version="1.0.0",
    description="Predicts monthly solar generation and expected cash received.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local network access (dev only)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(history.router, tags=["History"])
app.include_router(predict.router, tags=["Predictions"])
app.include_router(train.router,   tags=["Training"])


@app.get("/")
def root():
    return {"message": "SolarCast API is running. Visit /docs for the API reference."}
