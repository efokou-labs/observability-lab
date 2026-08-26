# observability-lab

Instrumented demo whose job is to prove metrics, logs, and traces can identify production failure modes.

## Signals

```text
App --> metrics --> Prometheus --+
    --> logs    --> Loki --------+--> Grafana
    --> traces  --> OTel --> Tempo
```

Dashboards cover **RED** (rate, errors, duration) and **USE** (utilization, saturation, errors).

## Verify

```bash
make verify
```

```bash
docker compose up
```

Inject failures with `FAILURE_MODE` (see kubernetes-operations-toolkit) and follow the telemetry to the cause.

Kind install is optional; the shared cluster already bootstraps an OTel collector in cloud-platform-blueprint. This repo supplies dashboards and the demo app.
