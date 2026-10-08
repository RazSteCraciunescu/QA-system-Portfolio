#!/usr/bin/env sh
set -eu
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
printf '\nSetup complete. Activate with: . .venv/bin/activate\n'
