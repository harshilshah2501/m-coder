# v12 Evaluation Workflow

## Overview
This document outlines the end-to-end workflow for validating the **Motadata Coder v12** model. It covers Training, Deployment, Benchmarking, and Analysis.

## Phase 1: Training (Execution)
**Goal:** Produce the v12 model checkpoint.

1.  **Prepare Environment:**
    Ensure `transformers`, `trl`, `peft` are installed.
2.  **Run Training Script:**
    ```bash
    cd /home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning
    python3 train_v12.py
    ```
    *   **Input:** `v12_combined.jsonl` (2,514 examples)
    *   **Base Model:** `Qwen/Qwen2.5-Coder-7B-Instruct`
    *   **Output:** `./finetuning_output/motadata-coder-v12`

## Phase 2: Deployment (Inference)
**Goal:** Serve the model for the RAG system and Benchmark suite.

1.  **Update vLLM Service:**
    Edit your vLLM launch command to point to the new checkpoint.
    ```bash
    vllm serve /home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/finetuning/finetuning_output/motadata-coder-v12 \
      --port 8000 \
      --dtype bfloat16 \
      --trust-remote-code
    ```
2.  **Verify Availability:**
    ```bash
    curl http://localhost:8000/v1/models
    ```

## Phase 3: Benchmarking (Evaluation)
**Goal:** Measure performance on 10 Real-World Tasks.

1.  **Navigate to Evaluation Root:**
    ```bash
    cd /home/harshil/Harshil-PoCs/RAG-Datastore/evaluation
    ```
2.  **Run Full Benchmark:**
    ```bash
    python3 run_motadata_bench.py --model motadata-coder-v12
    ```
    *   **Config:** `motadata_tasks/task_manifest.json`
    *   **Tasks:** `motadata_tasks/tasks/*.yaml`
    *   **Output:** `results/v12_run/results.json`

3.  **Run Single Task (Debugging):**
    If a specific task fails, run it in isolation with verbose logging.
    ```bash
    python3 test_single_task.py --task_id mongodb_protocol_removal --verbose
    ```

## Phase 4: Analysis & Iteration
**Goal:** Understand failures and improve.

1.  **Generate Failure Report:**
    ```bash
    python3 analyze_failures.py --results results/v12_run/results.json
    ```
2.  **Inspect Diffs:**
    Check `results/v12_run/diffs/` to see exactly what the model wrote vs what failed.
3.  **Review Logs:**
    Check `logs/v12_run/` for RAG context retrieval issues or system prompt violations.

## Key Files Reference

| File | Purpose |
|------|---------|
| `evaluation/finetuning/train_v12.py` | **Training Script** (The Start) |
| `evaluation/finetuning/v12_combined.jsonl` | **Dataset** (The Knowledge) |
| `evaluation/run_motadata_bench.py` | **Main Runner** (The Test) |
| `evaluation/task_executor.py` | **Logic** (Result Validation) |
| `rag-system/rag_api.py` | **Inference** (The Brain) |
