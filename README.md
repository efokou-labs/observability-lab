# observability-lab

Instrumented demo whose job is to prove metrics, logs, and traces can identify production failure modes.

## Signals

```text
App --> metrics --> Prometheus --+
    --> logs    --> Promtail --> Loki --+--> Grafana
    --> traces  --> OTel --> Tempo ----+
```

Dashboards cover **RED** (rate, errors, duration) and **USE** (utilization, saturation, errors).

## Verify

```bash
make verify
```

```bash
docker compose up --build
```

- App: http://localhost:8080/work
- Grafana: http://localhost:3001 (admin / admin), dashboard **RED and USE**
- Prometheus: http://localhost:9090

Grafana is on **3001** so it does not collide with other labs on 3000.

## Inject a failure

Same `FAILURE_MODE` values as [kubernetes-operations-toolkit](https://github.com/efokou-labs/kubernetes-operations-toolkit):

| Value | Symptom | What to look at |
| --- | --- | --- |
| `none` | Healthy `/work` | Rate of 200s |
| `http500` | `/work` returns 500 | Errors panel, logs `code: 500` |
| `latency` | `/work` sleeps (`LATENCY_SECONDS`, default 0.5s) | Duration p99, Tempo spans |
| `readiness` | `/readyz` returns 503 | Kubernetes Ready; Compose still serves `/work` |
| `dependency` | `/work` returns 502 | Errors, traces marked error |
| `cpu` | Short spin on `/work` | CPU panel |
| `memory` | Bounded allocation on `/work` | Memory panel |

```bash
make inject MODE=http500
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/work
```

Load the endpoint a few times, then open Grafana. Follow logs (`job="observability-lab"`) and traces (`service.name=observability-lab`) to the injected mode.

Kind install is optional. The shared cluster already bootstraps an OTel collector in cloud-platform-blueprint (`observability` namespace). This repo supplies the demo app, dashboards, and the Compose stack.

On kind, set `FAILURE_MODE` on the `obs-lab` Deployment and scrape `/metrics`. Point `OTEL_EXPORTER_OTLP_ENDPOINT` at `http://otel-collector.observability.svc.cluster.local:4318`.

## License

The source code for this project is licensed under the MIT License. Personal content, including my resume, photographs, written content, branding, and other identifying materials, is not covered by this license and may not be reused without permission.

See [LICENSE](LICENSE).
