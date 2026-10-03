# syntax=docker/dockerfile:1

# ── Build stage: install dependencies into a virtual environment ─────────────
FROM python:3.14-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Dependencies change far less often than code, so they get their own layer.
COPY requirements.txt .
RUN pip install -r requirements.txt


# ── Runtime stage: only the virtual environment and the application code ─────
FROM python:3.14-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    SOLARCAST_DATA_DIR=/data \
    SOLARCAST_MODELS_DIR=/models

# Run as an unprivileged user. /data is mounted read-only at run time;
# /models is the only place the application writes to.
RUN groupadd --gid 10001 solarcast \
 && useradd --uid 10001 --gid solarcast --no-create-home --shell /usr/sbin/nologin solarcast \
 && mkdir -p /data /models \
 && chown solarcast:solarcast /data /models

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY settings.py ./
COPY api ./api
COPY model ./model
# The image runs as a non-root user, so the code must be world-readable
# whatever permissions the files had on the machine that built it.
RUN chmod -R a+rX /app

USER 10001:10001
EXPOSE 8000
VOLUME ["/models"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --start-interval=2s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
