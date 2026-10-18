import json
import logging
import os
import resource
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Status, StatusCode

REQS = Counter("demo_requests_total", "Demo /work requests", ["code", "mode"])
LAT = Histogram(
    "demo_request_seconds",
    "Demo /work latency",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
IN_FLIGHT = Gauge("demo_in_flight", "In-flight /work requests")
MODE_INFO = Gauge("demo_failure_mode_info", "Active FAILURE_MODE (1 = selected)", ["mode"])
RSS = Gauge("demo_rss_bytes", "Resident set size in bytes")
CPU_SECONDS = Gauge("demo_cpu_seconds", "Process user+system CPU seconds")
OPEN_FDS = Gauge("demo_open_fds", "Open file descriptors")

KNOWN_MODES = ("none", "http500", "latency", "readiness", "dependency", "cpu", "memory")


class JsonLog(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            payload["trace_id"] = format(ctx.trace_id, "032x")
            payload["span_id"] = format(ctx.span_id, "016x")
        extra = getattr(record, "otel", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload)


def configure_logging() -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLog())
    log = logging.getLogger("observability-lab")
    log.handlers = [handler]
    log.setLevel(logging.INFO)
    log.propagate = False
    return log


def configure_tracing() -> trace.Tracer:
    resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "observability-lab")})
    provider = TracerProvider(resource=resource)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))
    elif os.getenv("OTEL_CONSOLE_SPANS") == "1":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    return trace.get_tracer("observability-lab")


LOG = configure_logging()
TRACER = configure_tracing()


def failure_mode() -> str:
    mode = os.getenv("FAILURE_MODE", "none").strip() or "none"
    return mode if mode in KNOWN_MODES else "none"


def sample_use() -> None:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = usage.ru_maxrss
    if sys.platform != "darwin":
        rss *= 1024
    RSS.set(rss)
    CPU_SECONDS.set(usage.ru_utime + usage.ru_stime)
    try:
        OPEN_FDS.set(len(os.listdir("/dev/fd")))
    except OSError:
        OPEN_FDS.set(0)


def refresh_mode_metric() -> str:
    mode = failure_mode()
    for known in KNOWN_MODES:
        MODE_INFO.labels(mode=known).set(1 if known == mode else 0)
    sample_use()
    return mode


@asynccontextmanager
async def lifespan(_: FastAPI):
    refresh_mode_metric()
    yield


app = FastAPI(title="observability-lab", lifespan=lifespan)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    if failure_mode() == "readiness":
        raise HTTPException(status_code=503, detail="readiness injection")
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def _inject(mode: str) -> None:
    if mode == "http500":
        raise HTTPException(status_code=500, detail="injected")
    if mode == "dependency":
        raise HTTPException(status_code=502, detail="upstream unavailable")
    if mode == "latency":
        time.sleep(float(os.getenv("LATENCY_SECONDS", "0.5")))
    if mode == "cpu":
        deadline = time.time() + float(os.getenv("CPU_SECONDS", "0.2"))
        while time.time() < deadline:
            _ = sum(i * i for i in range(4000))
    if mode == "memory":
        _blob = bytearray(int(os.getenv("MEMORY_BYTES", str(8 * 1024 * 1024))))
        del _blob


@app.get("/work")
def work(request: Request):
    mode = refresh_mode_metric()
    IN_FLIGHT.inc()
    start = time.perf_counter()
    code = "500"
    with TRACER.start_as_current_span("GET /work") as span:
        span.set_attribute("http.route", "/work")
        span.set_attribute("failure.mode", mode)
        try:
            _inject(mode)
            code = "200"
            return {"mode": mode}
        except HTTPException as exc:
            code = str(exc.status_code)
            span.set_status(Status(StatusCode.ERROR))
            span.set_attribute("http.status_code", exc.status_code)
            raise
        finally:
            duration = time.perf_counter() - start
            IN_FLIGHT.dec()
            LAT.observe(duration)
            REQS.labels(code, mode).inc()
            span.set_attribute("http.status_code", int(code))
            LOG.info(
                "work",
                extra={
                    "otel": {
                        "mode": mode,
                        "path": "/work",
                        "code": int(code),
                        "duration_ms": round(duration * 1000, 3),
                        "client": request.client.host if request.client else "",
                    }
                },
            )
