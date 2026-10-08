from __future__ import annotations

import argparse
import time
from urllib.error import URLError
from urllib.request import urlopen


def wait(url: str, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1.0) as response:  # noqa: S310 - operator-supplied URL
                if 200 <= response.status < 300:
                    return True
        except (URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(0.25)
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wait until an HTTP endpoint returns a 2xx status")
    parser.add_argument("url")
    parser.add_argument(
        "legacy_timeout",
        nargs="?",
        type=float,
        help="Timeout in seconds; retained for the existing shell and batch scripts",
    )
    parser.add_argument("--timeout", dest="named_timeout", type=float)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timeout = args.named_timeout if args.named_timeout is not None else args.legacy_timeout
    timeout = 30.0 if timeout is None else timeout
    if wait(args.url, timeout):
        print(f"Ready: {args.url}")
        return 0
    print(f"Timed out waiting for: {args.url}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
