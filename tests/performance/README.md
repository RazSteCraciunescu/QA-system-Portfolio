# Performance smoke profile

This is a small service-level check, not a capacity claim. It verifies that the gateway remains responsive while accepting concurrent work.

Run against the Docker environment:

```bash
docker run --rm -i --network host -e BASE_URL=http://127.0.0.1:8080 \
  grafana/k6 run - < tests/performance/smoke.js
```

On Docker Desktop, use `http://host.docker.internal:8080` instead of host networking.
