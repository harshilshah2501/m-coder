# `mapping_request_ids.md` — request_id spine (audit pack)

**What this is:** One place that ties each **Host-A scenario** to a **`request_id`** and log lines (Plan-Gate, Context Layer). Required for **audit-grade** closure alongside per-scenario folders and validation sheets — see [HOST_A_PROOF_PACK_CLOSURE.md](./HOST_A_PROOF_PACK_CLOSURE.md).

**Where to put it:** Copy this file to your evidence root, e.g. `~/hostA_proof_pack_<date>/mapping_request_ids.md`, and fill the table. Keep the repo copy here as a **template**; your filled version may live outside `m-coder`.

**Worked example (partial fill from a real session):** [HOST_A_PLAN_GATE_LOG_MAPPING.md](./HOST_A_PLAN_GATE_LOG_MAPPING.md).

---

## Session metadata (fill in)

| Field | Value |
|-------|--------|
| Date | |
| Host / IDE | (e.g. JetBrains WSL backend) |
| MOTADATA_ROOT | |
| MCODER_ROOT | |

---

## Mapping table (fill in)

| Scenario | request_id | Matched by (time / query / route) | Plan-Gate line ref | Context Layer line ref |
|----------|------------|-----------------------------------|--------------------|-------------------------|
| Ask (5.1) | | | | |
| Explain/Debug (5.2) | | | | |
| Execute OK | | | | |
| Execute Blocked | | | | |
| Execute Failed | | | | |
| No-match (5.4) | | | | |
| Failure (5.5) | | optional / `NOT_PROVEN` if only curl proof | | n/a |

If you cannot correlate a cell, use **`NOT_PROVEN`** — that is an acceptable audit state until logs are aligned.

---

## Extraction commands (reminder)

```bash
cd "$MCODER_ROOT"
grep -i "request_id" .run/plan_gate.log | tail -80
```

Context Layer (path varies):

```bash
grep -E "export_evidence|request_id" /path/to/context_layer.log | tail -80
```
