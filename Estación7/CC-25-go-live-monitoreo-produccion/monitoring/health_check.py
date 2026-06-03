"""Production health check script — run on cron every 5min"""
import httpx
import sys
from datetime import datetime

ENDPOINTS = [
    ("GET", "/health", 200),
    ("POST", "/auth/login", 200, {"email": "analista@example.com", "password": "password"}),
]


def run_checks(base_url: str) -> bool:
    all_ok = True
    print(f"[{datetime.utcnow().isoformat()}] Health checks — {base_url}")

    with httpx.Client(base_url=base_url, timeout=10) as client:
        for entry in ENDPOINTS:
            method, path, expected = entry[0], entry[1], entry[2]
            body = entry[3] if len(entry) > 3 else None

            try:
                if method == "GET":
                    resp = client.get(path)
                else:
                    resp = client.post(path, json=body)

                ok = resp.status_code == expected
                status = "PASS" if ok else "FAIL"
                print(f"  {status}  {method} {path} → {resp.status_code}")
                if not ok:
                    all_ok = False
            except Exception as e:
                print(f"  ERROR {method} {path} → {e}")
                all_ok = False

    return all_ok


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    ok = run_checks(url)
    sys.exit(0 if ok else 1)
