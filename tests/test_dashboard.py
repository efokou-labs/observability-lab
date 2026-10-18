import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_has_red_and_use_panels():
    dashboard = json.loads((ROOT / "grafana/dashboards/red-use.json").read_text())
    titles = {panel["title"] for panel in dashboard["panels"]}
    for needed in (
        "Rate",
        "Errors",
        "Duration p99",
        "CPU",
        "Memory",
        "Open FDs",
        "In flight",
        "Logs",
    ):
        assert needed in titles, needed
    exprs = " ".join(
        target.get("expr", "")
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
    )
    assert "demo_requests_total" in exprs
    assert "demo_cpu_seconds" in exprs
    assert "demo_rss_bytes" in exprs


def test_prometheus_scrapes_app_metrics():
    text = (ROOT / "prometheus.yml").read_text()
    assert "app:8080" in text
    assert "/metrics" in text or "metrics_path" not in text
