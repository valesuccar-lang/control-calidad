"""Load test — 50 VUs targeting /auth/login and /health.
Run: locust -f locustfile.py --headless -u 50 -r 10 --run-time 60s
"""
from locust import HttpUser, task, between


class QualityControlUser(HttpUser):
    wait_time = between(0.5, 1.5)
    token = None

    def on_start(self):
        resp = self.client.post("/auth/login", json={"email": "analista@example.com", "password": "password"})
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    @task(3)
    def health_check(self):
        self.client.get("/health")

    @task(2)
    def list_inspections(self):
        if self.token:
            self.client.get(
                "/api/inspections",
                headers={"Authorization": f"Bearer {self.token}"},
            )

    @task(1)
    def login(self):
        self.client.post("/auth/login", json={"email": "analista@example.com", "password": "password"})
