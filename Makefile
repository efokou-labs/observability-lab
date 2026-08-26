.PHONY: verify
verify:
	test -d .venv || python3 -m venv .venv
	.venv/bin/pip install -q -r requirements-dev.txt
	.venv/bin/pytest -q
	@echo observability-lab verify passed
