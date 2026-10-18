.PHONY: verify demo inject down

verify:
	test -d .venv || python3 -m venv .venv
	.venv/bin/pip install -q -r requirements-dev.txt
	.venv/bin/pytest -q
	@echo observability-lab verify passed

demo:
	docker compose up --build

inject:
	@test -n "$(MODE)" || (echo "MODE=none|http500|latency|readiness|dependency|cpu|memory"; exit 1)
	FAILURE_MODE=$(MODE) docker compose up --build -d
	@echo "injected FAILURE_MODE=$(MODE)"
	@echo "app     http://localhost:8080/work"
	@echo "metrics http://localhost:8080/metrics"
	@echo "grafana http://localhost:3001 (admin/admin) dashboard RED and USE"

down:
	docker compose down
