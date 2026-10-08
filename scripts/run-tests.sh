#!/usr/bin/env sh
set -eu
python -m pytest -m 'unit or component or contract or security' \
  --cov=app --cov-report=term-missing --cov-report=xml:artifacts/coverage.xml \
  --junitxml=artifacts/fast-tests-junit.xml
RUN_INTEGRATION=1 BASE_URL=http://127.0.0.1:8080 \
  PARTNER_BASE_URL=http://127.0.0.1:8083 \
  python -m pytest -m integration --junitxml=artifacts/integration-junit.xml
robot --outputdir artifacts/robot tests/robot
