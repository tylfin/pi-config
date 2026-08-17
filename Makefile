UV ?= uv
PYTEST_ARGS ?=

.PHONY: evals login

evals:
	$(UV) run --quiet --no-project --with-requirements requirements.txt pytest -q evals $(PYTEST_ARGS)

login:
	PI_CODING_AGENT_DIR=$(CURDIR) pi
