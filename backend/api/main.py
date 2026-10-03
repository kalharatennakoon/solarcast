import sys
from pathlib import Path

# Add backend/ to sys.path so model/ and api/ packages resolve correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from api.metrics import metrics_middleware, metrics_response  # noqa: E402
from api.model_store import model_store  # noqa: E402
from api.routes import health, history, predict, train  # noqa: E402
from settings import get_settings  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once at startup instead of on the first request.
    model_store.get()
    yield


app = FastAPI(
    title="SolarCast API",
    version="1.1.0",
    description="Predicts monthly solar generation and expected cash received.",
    lifespan=lifespan,
)

# Browsers only need CORS when the frontend is served from a different origin
# than the API. Behind the Vite dev proxy or nginx the two share an origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.middleware("http")(metrics_middleware)

app.include_router(health.router,  tags=["Health"])
app.include_router(history.router, tags=["History"])
app.include_router(predict.router, tags=["Predictions"])
app.include_router(train.router,   tags=["Training"])


@app.get("/metrics", include_in_schema=False)
def metrics():
    return metrics_response()


@app.get("/")
def root():
    return {"message": "SolarCast API is running. Visit /docs for the API reference."}
