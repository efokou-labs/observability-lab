import os

from fastapi.testclient import TestClient

from app.main import KNOWN_MODES, app

client = TestClient(app)


def test_healthz():
    assert client.get("/healthz").json()["status"] == "ok"


def test_readyz_ok(monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "none")
    assert client.get("/readyz").status_code == 200


def test_readyz_injected(monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "readiness")
    assert client.get("/readyz").status_code == 503


def test_work_ok_increments_200(monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "none")
    assert client.get("/work").json()["mode"] == "none"
    body = client.get("/metrics").text
    assert "demo_requests_total" in body
    assert 'code="200"' in body
    assert "demo_request_seconds" in body
    assert "demo_cpu_seconds" in body
    assert "demo_rss_bytes" in body
    assert "demo_open_fds" in body


def test_http500_increments_error_counter(monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "http500")
    assert client.get("/work").status_code == 500
    body = client.get("/metrics").text
    assert 'demo_requests_total{code="500",mode="http500"}' in body


def test_dependency_is_502(monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "dependency")
    assert client.get("/work").status_code == 502
    assert 'code="502"' in client.get("/metrics").text


def test_latency_records_duration(monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "latency")
    monkeypatch.setenv("LATENCY_SECONDS", "0.02")
    assert client.get("/work").status_code == 200
    body = client.get("/metrics").text
    assert "demo_request_seconds_count" in body


def test_cpu_and_memory_stay_bounded(monkeypatch):
    monkeypatch.setenv("CPU_SECONDS", "0.01")
    monkeypatch.setenv("MEMORY_BYTES", "1024")
    monkeypatch.setenv("FAILURE_MODE", "cpu")
    assert client.get("/work").status_code == 200
    monkeypatch.setenv("FAILURE_MODE", "memory")
    assert client.get("/work").status_code == 200


def test_unknown_mode_is_none(monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "not-a-mode")
    assert client.get("/work").json()["mode"] == "none"


def test_mode_info_metric(monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "http500")
    client.get("/work")
    body = client.get("/metrics").text
    for mode in KNOWN_MODES:
        needle = f'demo_failure_mode_info{{mode="{mode}"}}'
        assert needle in body
    assert os.getenv("FAILURE_MODE") == "http500"
