# Common tasks for SolarCast. Run `make` to list them.

PYTHON ?= $(CURDIR)/.venv/bin/python

.DEFAULT_GOAL := help
.PHONY: help install lint test lock sample-data up up-sample down logs smoke

help: ## List available tasks
	@grep -E "^[a-z-]+:.*## " $(MAKEFILE_LIST) | awk -F ":.*## " '{printf "  %-13s %s\n", $$1, $$2}'

install: ## Install backend (into .venv) and frontend dependencies
	$(PYTHON) -m pip install -r backend/requirements-dev.txt
	cd frontend && npm ci

lint: ## Lint the backend with ruff
	cd backend && $(PYTHON) -m ruff check .

test: ## Run the backend test suite (synthetic data only)
	cd backend && $(PYTHON) -m pytest --cov --cov-report=term

lock: ## Regenerate backend/requirements.txt from requirements.in (needs uv)
	cd backend && uv pip compile requirements.in --universal --python-version 3.14 -o requirements.txt

sample-data: ## Regenerate the synthetic CSVs in backend/sample_data
	cd backend && $(PYTHON) scripts/generate_sample_data.py

up: ## Build and start the containers with your own data (backend/data)
	docker compose up --build --detach --wait
	@echo "Dashboard: http://localhost:8080   API docs: http://localhost:8000/docs"

up-sample: ## Build and start the containers with the synthetic sample data
	SOLARCAST_DATA_PATH=./backend/sample_data docker compose up --build --detach --wait
	@echo "Dashboard: http://localhost:8080   API docs: http://localhost:8000/docs"

down: ## Stop the containers (trained models are kept)
	docker compose down

logs: ## Follow container logs
	docker compose logs --follow

smoke: ## End-to-end check of the running containers (retrains the model)
	./scripts/smoke-test.sh
