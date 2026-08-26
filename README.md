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

## License

The source code for this project is licensed under the MIT License. Personal content, including my resume, photographs, written content, branding, and other identifying materials, is not covered by this license and may not be reused without permission.

See [LICENSE](LICENSE).

