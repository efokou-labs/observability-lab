import os
import time
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(title="observability-lab")
REQS = Counter("demo_requests_total", "requests", ["code"])
LAT = Histogram("demo_request_seconds", "latency")
MODE = os.getenv("FAILURE_MODE", "none")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/work")
@LAT.time()
def work():
    if MODE == "http500":
        REQS.labels("500").inc()
        raise HTTPException(status_code=500, detail="injected")
    if MODE == "latency":
        time.sleep(0.5)
    REQS.labels("200").inc()
    return {"mode": MODE}
