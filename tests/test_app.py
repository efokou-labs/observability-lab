from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_metrics_and_work():
    assert client.get("/healthz").status_code == 200
    assert client.get("/work").status_code == 200
    body = client.get("/metrics").text
    assert "demo_requests_total" in body
