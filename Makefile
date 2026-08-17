UV ?= uv
EVALS ?=

.PHONY: evals login

evals:
	$(UV) run --quiet --no-project --with-requirements requirements.txt python evals/run.py $(EVALS)

login:
	PI_CODING_AGENT_DIR=$(CURDIR) pi
