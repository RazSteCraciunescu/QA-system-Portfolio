.PHONY: setup lint fast integration ui robot postman validate up down clean

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements-dev.txt
	.venv/bin/python -m playwright install chromium

lint:
	ruff check app tests scripts
	ruff format --check app tests scripts
	mypy app

fast:
	pytest -m "unit or component or contract or security" --cov=app --cov-report=term-missing --cov-report=xml:artifacts/coverage.xml

integration:
	RUN_INTEGRATION=1 BASE_URL=http://127.0.0.1:8080 PARTNER_BASE_URL=http://127.0.0.1:8083 pytest -m integration

ui:
	RUN_UI=1 BASE_URL=http://127.0.0.1:8080 pytest -m ui

robot:
	robot --outputdir artifacts/robot tests/robot

postman:
	newman run tests/postman/relayhub.postman_collection.json -e tests/postman/relayhub.postman_environment.json

validate:
	python scripts/validate_repository.py

up:
	docker compose up -d --build --wait --wait-timeout 180
	python scripts/wait_for_service.py http://127.0.0.1:8080/health/ready 60

down:
	docker compose down

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov robot-results test-results
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
