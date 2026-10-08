from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "local-e2e"
DATABASE = ARTIFACTS / "relayhub-e2e.db"


def wait_for(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1.0) as response:  # noqa: S310 - local URL
                if 200 <= response.status < 300:
                    return
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.2)
    raise RuntimeError(f"Service did not become ready: {url}")


def terminate(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.monotonic() + 5
    for process in processes:
        while process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.1)
        if process.poll() is None:
            process.kill()


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    DATABASE.unlink(missing_ok=True)
    heartbeat = Path(tempfile.gettempdir()) / "relayhub-worker-heartbeat"
    heartbeat.unlink(missing_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(ROOT),
            "APP_ENV": "test",
            "DATABASE_URL": f"sqlite:///{DATABASE.as_posix()}",
            "GATEWAY_BASE_URL": "http://127.0.0.1:18080",
            "TRANSFORMER_URL": "http://127.0.0.1:18082",
            "PARTNER_URL": "http://127.0.0.1:18083",
            "PARTNER_ADMIN_TOKEN": "local-test-token",
            "WORKER_POLL_SECONDS": "0.05",
            "WORKER_RETRY_DELAY_SECONDS": "0.02",
            "LOG_LEVEL": "WARNING",
            "WORKER_HEARTBEAT_FILE": str(heartbeat),
            "TERM": env.get("TERM", "xterm"),
        }
    )

    commands = {
        "transformer": [
            sys.executable,
            "-m",
            "uvicorn",
            "app.transformer.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "18082",
        ],
        "partner": [
            sys.executable,
            "-m",
            "uvicorn",
            "app.partner_mock.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "18083",
        ],
        "gateway": [
            sys.executable,
            "-m",
            "uvicorn",
            "app.gateway.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "18080",
        ],
        "worker": [sys.executable, "-m", "app.worker.main"],
    }

    processes: list[subprocess.Popen] = []
    log_handles = []
    try:
        for name, command in commands.items():
            log_file = (ARTIFACTS / f"{name}.log").open("w", encoding="utf-8")
            log_handles.append(log_file)
            processes.append(
                subprocess.Popen(
                    command,
                    cwd=ROOT,
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                )
            )

        wait_for("http://127.0.0.1:18080/health/ready")
        wait_for("http://127.0.0.1:18083/health/ready")

        test_env = env | {
            "RUN_INTEGRATION": "1",
            "BASE_URL": "http://127.0.0.1:18080",
            "PARTNER_BASE_URL": "http://127.0.0.1:18083",
        }
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-m",
                "integration",
                "--junitxml=artifacts/local-e2e/integration-junit.xml",
            ],
            cwd=ROOT,
            env=test_env,
            check=False,
        )
        return result.returncode
    except Exception as exc:
        print(f"Local end-to-end verification failed: {exc}", file=sys.stderr)
        return 1
    finally:
        terminate(processes)
        for handle in log_handles:
            handle.close()
        heartbeat.unlink(missing_ok=True)
        if os.getenv("KEEP_E2E_DATABASE") != "1":
            DATABASE.unlink(missing_ok=True)
        shutil.rmtree(ROOT / "__pycache__", ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
