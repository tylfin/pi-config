UV ?= uv
PYTEST_ARGS ?=

.PHONY: evals lint typecheck check login

evals:
	$(UV) run pytest -q evals $(PYTEST_ARGS)

lint:
	$(UV) run ruff check evals

typecheck:
	$(UV) run ty check evals

check: lint typecheck evals

login:
	PI_CODING_AGENT_DIR=$(CURDIR) pi
