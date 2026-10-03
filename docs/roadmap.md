# Roadmap — SolarCast as a GitOps MLOps platform

SolarCast started as a forecasting app. This roadmap turns it into a small but
complete MLOps platform: the model is built, tested, deployed, monitored and
retrained through automated pipelines, with Git as the single source of truth
for what runs in the cluster.

Everything runs locally and for free: Docker Desktop's built-in Kubernetes,
GitHub Actions and Docker Hub. The same manifests can later move to a managed
cloud cluster.

## Phases

| Phase | What gets built | What it demonstrates |
|---|---|---|
| **1. Harden and containerise** | API fixes, test suite, Dockerfiles, Compose file, CI pipeline | `docker compose up` runs the whole app; every pull request is linted, tested, built, scanned and smoke-tested |
| **2. Kubernetes and GitOps** | Manifests for dev and prod, Argo CD, CI that updates the deployed image tag | A merge to `main` reaches the cluster with no manual `kubectl` |
| **3. Data and model lifecycle** | MinIO for private data, daily inverter ingestion with validation, weather features, MLflow tracking and registry, training as a cluster job | A versioned model with recorded metrics, compared against a naive baseline |
| **4. Observability** | Prometheus, Grafana dashboards, alerts for the API and for forecast error | Live dashboards of latency, errors and prediction accuracy |
| **5. Automated retraining and safe rollout** | Scheduled retraining, a promotion gate, canary releases with Argo Rollouts, drift detection | A bad model or a bad release rolls itself back |
| **6. Showcase** | Architecture diagram, recorded demo, write-up, optional Terraform for a cloud cluster | A repository that explains itself in two minutes |

## Design decisions

- **One repository.** Kubernetes manifests will live in `deploy/` next to the
  code, so the whole system can be read in one place.
- **Private data stays out of Git.** The real inverter CSVs are never
  committed or baked into an image. They are mounted at run time (phase 1) and
  will live in MinIO (phase 3). Tests and CI use the synthetic
  `backend/sample_data` set.
- **Images are built once and promoted.** CI tags every image with the commit
  SHA; environments differ only in configuration.
- **Training moves out of the API.** In phase 1 the API still trains on
  `POST /train`. From phase 3 training is a separate job that publishes to a
  model registry, and the API only serves.

## Phase 1 — what changed

- **Dependencies** — direct dependencies in `requirements.in`, fully pinned in
  `requirements.txt`; five unused packages removed; dev tooling split out.
- **Configuration** — data folder, models folder, CORS origins and the unit
  rate come from environment variables (`backend/settings.py`).
- **API** — the model is loaded once and cached, and reloaded when the model
  file changes; `months` is validated (1–12); liveness, readiness and
  Prometheus metrics endpoints; CORS restricted to configured origins; only
  one training run at a time; artefacts written atomically.
- **Tests** — 35 pytest tests covering preprocessing, the model pipeline and
  the API, running on synthetic data.
- **Containers** — multi-stage, non-root images; nginx serves the dashboard
  and proxies `/api`; Compose runs the backend with a read-only filesystem.
- **CI** — lint, test, build, Trivy scan, container smoke test; multi-arch
  images published to Docker Hub from `main`.

## Known gaps carried forward

- `POST /train` is unauthenticated. It is removed from the public API in
  phase 3, when training becomes a cluster job.
- The model is trained on roughly two years of monthly data and only narrowly
  beats a "same month last year" baseline. Phase 3 moves to daily data with
  weather features and adds a proper baseline comparison.
