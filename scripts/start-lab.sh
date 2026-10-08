#!/usr/bin/env sh
set -eu
docker compose up -d --build --wait --wait-timeout 180
python3 scripts/wait_for_service.py http://127.0.0.1:8080/health/ready 60
printf 'RelayHub is ready at http://127.0.0.1:8080\n'
