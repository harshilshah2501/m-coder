# m-coder Makefile — DVC artifact topology (checkpoints, datasets)
# Usage: make dvc-push-checkpoints RUN_ID=phase08D
#        make dvc-pull-dataset FREEZE_ID=golden_v1

REPO_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || echo .)
ARTIFACTS := $(REPO_ROOT)/ml/artifacts
CHECKPOINTS_DIR := $(ARTIFACTS)/checkpoints
DATASETS_DIR := $(ARTIFACTS)/datasets

.PHONY: dvc-push-checkpoints dvc-pull-checkpoints dvc-push-dataset dvc-pull-dataset dvc-init graph-up graph-refresh graph-status graph-logs graph-down cig-smoke

# Ensure DVC is initialized with localstore (local disk) as default
dvc-init:
	@cd "$(REPO_ROOT)" && ./scripts/setup_dvc_local.sh

# --- Checkpoints ---
dvc-push-checkpoints:
	@test -n "$(RUN_ID)" || (echo "Usage: make dvc-push-checkpoints RUN_ID=<run_id>"; exit 1)
	@cd "$(REPO_ROOT)" && \
		DIR="$(CHECKPOINTS_DIR)/$(RUN_ID)"; \
		test -d "$$DIR" || (echo "Error: $$DIR not found"; exit 1); \
		if [ ! -f "$$DIR.dvc" ]; then dvc add "$$DIR"; fi; \
		git add "$$DIR.dvc" 2>/dev/null || true; \
		dvc push "$$DIR.dvc"; \
		echo "--- Verification commands ---"; \
		echo "  ls -la $$DIR/"; \
		echo "  sha256sum $$DIR/checkpoint-*/*.safetensors 2>/dev/null || true"

dvc-pull-checkpoints:
	@test -n "$(RUN_ID)" || (echo "Usage: make dvc-pull-checkpoints RUN_ID=<run_id>"; exit 1)
	@cd "$(REPO_ROOT)" && \
		DVC_FILE="$(CHECKPOINTS_DIR)/$(RUN_ID).dvc"; \
		test -f "$$DVC_FILE" || (echo "Error: $$DVC_FILE not found. Commit the .dvc file first."; exit 1); \
		dvc pull "$$DVC_FILE"; \
		echo "--- Verification commands ---"; \
		echo "  ls -la $(CHECKPOINTS_DIR)/$(RUN_ID)/"; \
		echo "  sha256sum $(CHECKPOINTS_DIR)/$(RUN_ID)/checkpoint-*/*.safetensors 2>/dev/null || true"

# --- Datasets ---
dvc-push-dataset:
	@test -n "$(FREEZE_ID)" || (echo "Usage: make dvc-push-dataset FREEZE_ID=<freeze_id>"; exit 1)
	@cd "$(REPO_ROOT)" && \
		DIR="$(DATASETS_DIR)/$(FREEZE_ID)"; \
		test -d "$$DIR" || (echo "Error: $$DIR not found"; exit 1); \
		if [ ! -f "$$DIR.dvc" ]; then dvc add "$$DIR"; fi; \
		git add "$$DIR.dvc" 2>/dev/null || true; \
		dvc push "$$DIR.dvc"; \
		echo "--- Verification commands ---"; \
		echo "  ls -la $$DIR/"; \
		echo "  sha256sum $$DIR/*.jsonl 2>/dev/null || true"

dvc-pull-dataset:
	@test -n "$(FREEZE_ID)" || (echo "Usage: make dvc-pull-dataset FREEZE_ID=<freeze_id>"; exit 1)
	@cd "$(REPO_ROOT)" && \
		DVC_FILE="$(DATASETS_DIR)/$(FREEZE_ID).dvc"; \
		test -f "$$DVC_FILE" || (echo "Error: $$DVC_FILE not found. Commit the .dvc file first."; exit 1); \
		dvc pull "$$DVC_FILE"; \
		echo "--- Verification commands ---"; \
		echo "  ls -la $(DATASETS_DIR)/$(FREEZE_ID)/"; \
		echo "  sha256sum $(DATASETS_DIR)/$(FREEZE_ID)/*.jsonl 2>/dev/null || true"

graph-up:
	@cd "$(REPO_ROOT)" && ./scripts/graph_stack.sh up

graph-refresh:
	@cd "$(REPO_ROOT)" && ./scripts/graph_stack.sh refresh

graph-status:
	@cd "$(REPO_ROOT)" && ./scripts/graph_stack.sh status

graph-logs:
	@cd "$(REPO_ROOT)" && ./scripts/graph_stack.sh logs

graph-down:
	@cd "$(REPO_ROOT)" && ./scripts/graph_stack.sh down

cig-smoke:
	@cd "$(REPO_ROOT)" && PYTHONPATH=. pytest -q runtime/tests/test_code_intelligence_graph_smoke.py
