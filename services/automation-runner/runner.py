#!/usr/bin/env python3
"""Automation runner: health-check API, fetch script manifests with shared secret (extend with subprocess)."""
import os
import time

import httpx

API_URL = os.environ.get("API_URL", "http://api:8000").rstrip("/")
SECRET = os.environ.get("AUTOMATION_RUNNER_SECRET", "")


def main() -> None:
    while True:
        try:
            r = httpx.get(f"{API_URL}/health", timeout=10.0)
            print(f"api health: {r.status_code}")
            if SECRET:
                m = httpx.get(
                    f"{API_URL}/api/v1/internal/scripts/1/manifest",
                    headers={"X-Automation-Secret": SECRET},
                    timeout=10.0,
                )
                print(f"manifest sample: {m.status_code}")
        except Exception as e:
            print(f"runner error: {e}")
        time.sleep(60)


if __name__ == "__main__":
    main()
