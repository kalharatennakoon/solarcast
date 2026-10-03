"""
Prometheus metrics for the SolarCast API, exposed at GET /metrics.

HTTP metrics are labelled with the route template (e.g. "/predict"), never the
raw URL, so the number of time series stays small and bounded.
"""

import time

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

HTTP_REQUESTS = Counter(
    "solarcast_http_requests_total",
    "HTTP requests handled, by method, route and status code.",
    ["method", "path", "status"],
)
HTTP_DURATION = Histogram(
    "solarcast_http_request_duration_seconds",
    "HTTP request duration in seconds, by method and route.",
    ["method", "path"],
)
PREDICTED_MONTHS = Counter(
    "solarcast_predicted_months_total",
    "Forecast months served by GET /predict.",
)
TRAINING_RUNS = Counter(
    "solarcast_training_runs_total",
    "Training runs started through POST /train, by outcome.",
    ["outcome"],
)
TRAINING_DURATION = Histogram(
    "solarcast_training_duration_seconds",
    "Wall-clock duration of successful training runs.",
    buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300),
)
MODEL_LOADED = Gauge(
    "solarcast_model_loaded",
    "1 if a trained model is loaded in this process, otherwise 0.",
)
MODEL_TRAINED_TIMESTAMP = Gauge(
    "solarcast_model_trained_timestamp_seconds",
    "Unix time at which the loaded model file was written.",
)

_UNINSTRUMENTED = {"/metrics"}


async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        if path not in _UNINSTRUMENTED:
            HTTP_REQUESTS.labels(request.method, path, str(status)).inc()
            HTTP_DURATION.labels(request.method, path).observe(
                time.perf_counter() - start
            )


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
