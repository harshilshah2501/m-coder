# Host-A — `request_id` mapping (filled from `plan_gate.log` excerpt)

**Source:** `PLAN_GATE` / `EXPLAIN_DEBUG` lines from a prior run (same ordering as `terminals/3.txt` excerpt).  
**Use:** Copy into `hostA_proof_pack/mapping_request_ids.md` or attach to your audit packet.

**Session notes (confirmed)**

- **Execute (plugin, Host-A §5.3 order):** OK → BLOCKED → FAILED maps to the **first three** `/v0/execute` lines in time order: `req-8c58bfd9-…` → `req-e6cbc5d4-…` → `req-a9e7b5a1-…`.  
- **Execute (named replays):** `audit-echo-test-1` and `hostA-exec-ok-sample` are **separate** successful executes (e.g. `curl` / doc samples), **not** the BLOCKED/FAILED plugin cases.  
- **No-match (5.4):** `req-a8d963fa-1070-4f04-b33c-66b65cc4107a`.

**Legend**

| Confidence | Meaning |
|------------|---------|
| **High** | Structure of the log fixes the label (e.g. `EXPLAIN_DEBUG` + same `request_id` on `/v1/ask`). |
| **Medium** | Path and id are explicit (`/v0/execute`, named ids like `hostA-exec-ok-sample`). |
| **Low** | `/v1/ask` only — could be plain Ask, No-match, or other; **match by wall-clock time** to your `Ask_v1.md` / `NoMatch.md` / IDE session notes. |

---

## 1. Explain / Debug (HIGH)

Same `request_id` appears on `runtime.ask_service.reasoner EXPLAIN_DEBUG` and `PLAN_GATE … path=/v1/ask`.

| request_id | Scenario | Plan-Gate `duration_ms` (approx) | Notes |
|------------|----------|-----------------------------------|--------|
| `req-afb80681-79b1-4d90-99c5-d25610c7c7ea` | Explain/Debug | ~4249 | vLLM ~4248 ms |
| `req-cfd3b602-a6cb-4af5-abc0-a5ade11e924a` | Explain/Debug | ~3374 | vLLM ~3372 ms |
| `req-ba28597e-565c-47ae-95f2-62a8d956473f` | Explain/Debug | ~5405 | vLLM ~5403 ms |
| `req-434f1da1-d5f6-45dc-97f8-384959a66df4` | Explain/Debug | ~5985 | vLLM ~5984 ms |

---

## 2. Execute (MEDIUM → HIGH for plugin triple)

| request_id | Scenario | `duration_ms` (approx) | Notes |
|------------|----------|------------------------|--------|
| `req-8c58bfd9-bab1-477b-9d1d-d4012cedbf5a` | **Execute OK** (5.3) | ~131 | First plugin execute in session; `status=success` in log. |
| `req-e6cbc5d4-f0ea-4a31-9a62-e3f67783ad53` | **Execute BLOCKED** (5.3) | ~127 | Second plugin execute; policy block path. |
| `req-a9e7b5a1-c711-4394-a77b-448b124cdb52` | **Execute FAILED** (5.3) | ~0.6 | Third plugin execute; sandbox ran, non-success outcome (see `Exec_Runtime.md`). |
| `audit-echo-test-1` | Execute — audit / `curl` replay | ~263 | Named id; **not** one of the three plugin governance cases above. |
| `hostA-exec-ok-sample` | Execute — Host-A doc sample (`echo` style) | ~261 | ACTION_7 **sample** naming; **not** the BLOCKED/FAILED rows. |
| `req-24029510-486e-44ed-a6aa-b47dfa67409d` | Execute — additional | ~0.5 | Appears later in log; correlate with command if needed. |

---

## 3. Ask v1 only — `/v1/ask` without `EXPLAIN_DEBUG` lines

These are **evidence-first Ask** (`request_type=ask_v1`) in the log. **No-match (5.4)** is labeled where confirmed; remaining rows are **Ask (5.1)** unless you add more notes.

**Order in log (chronological)**

| # | request_id | duration_ms (approx) | Label |
|---|------------|----------------------|--------|
| 1 | `req-6ef1a81e-e245-49c8-9cb2-b63d650585c7` | 5.7 | Ask (5.1) |
| 2 | `req-c059b113-5077-4ef9-87a0-9d4b96e36dcb` | 215 | Ask (5.1) |
| 3 | `req-d7220005-d4f0-4d4a-a436-97933569ed03` | 1.6 | Ask (5.1) |
| 4 | `req-9b8cafe5-ff7a-443f-bf04-31125abc643d` | 1.7 | Ask (5.1) |
| 5 | `req-dfc5d127-0ca2-4320-a0fe-dedc44e04ca4` | 1.6 | Ask (5.1) |
| 6 | `req-7ededef2-69a4-41b0-84c8-e809980fc366` | 174 | Ask (5.1) |
| 7 | `req-b0a27e2c-e09b-4a49-851d-1a5e40bacd54` | 173 | Ask (5.1) |
| 8 | `req-0bee9763-1735-4717-860d-ffc5f49f55d6` | 1.6 | Ask (5.1) |
| 9 | `req-b009be96-023a-4b6e-bf0a-9404d45d2771` | 168 | Ask (5.1) |
| 10 | `req-2b9a060c-c330-4b2c-b6d4-a32c66c54271` | 87 | Ask (5.1) |
| 11 | `req-cefdd748-cfd2-4957-816e-847a652930bf` | 1.6 | Ask (5.1) |
| 12 | `req-debd1f88-6b2c-46ff-aa20-59ac09fd2b21` | 104 | Ask (5.1) |
| 13 | `req-4d6cdecd-6771-473e-864a-bfc9e68e9b51` | 1.4 | Ask (5.1) |
| 14 | `req-8dda3583-af7f-430e-be19-1d8b51c0b6b6` | 1.4 | Ask (5.1) |
| 15 | `req-de22e871-6e63-4f93-9b8b-e5b0b6457d3e` | 1.4 | Ask (5.1) |
| 16 | `req-56a623c2-8ff0-4496-8616-8812b1f42dfc` | 122 | Ask (5.1) |
| 17 | `req-a8d963fa-1070-4f04-b33c-66b65cc4107a` | 77 | **No-match (5.4)** — confirmed |
| 18 | `req-322b36c3-7808-4b56-ad59-7a3671cfed2d` | 1.3 | Ask (5.1) |
| 19 | `req-4fec513d-8c48-4ad3-9da8-87580af77615` | 1.3 | Ask (5.1) |

**Heuristic:** Longer `duration_ms` on `/v1/ask` without `EXPLAIN_DEBUG` often means **Context Layer + planning**; sub‑2 ms lines are often **fast** responses. No-match still uses `/v1/ask` — correlation is by **session note**, not duration alone.

---

## 4. Failure mode (5.5)

**Not present** in this excerpt (no failed health / error path). Keep **NOT_PROVEN** for Plan-Gate `request_id` on failure, or add a line when you capture a failing Ask during outage.

---

## 5. STEP 6 trace matrix — paste-friendly (partial)

| Scenario | request_id | Plugin | Context Layer | Plan-Gate | vLLM |
|----------|------------|--------|---------------|-----------|------|
| Ask (5.1) | *(any row in §3 marked Ask)* | Y* | Y* | Y | n/a |
| No-match (5.4) | `req-a8d963fa-1070-4f04-b33c-66b65cc4107a` | Y* | Y* | Y | n/a |
| Explain/Debug (5.2) | e.g. `req-afb80681-79b1-4d90-99c5-d25610c7c7ea` | Y* | Y* | Y | Y |
| Execute OK | `req-8c58bfd9-bab1-477b-9d1d-d4012cedbf5a` | Y | n/a | Y | n/a |
| Execute BLOCKED | `req-e6cbc5d4-f0ea-4a31-9a62-e3f67783ad53` | Y | n/a | Y | n/a |
| Execute FAILED | `req-a9e7b5a1-c711-4394-a77b-448b124cdb52` | Y | n/a | Y | n/a |
| Execute (curl sample) | `hostA-exec-ok-sample` | optional | n/a | Y | n/a |

\* *Confirm from artifacts; plugin shows `request_id` in 0.2.6+.*

---

## 6. Next step for you (WSL)

1. Optional: tag additional **§3** rows as No-match if you have more than one synthetic query in the session.  
2. Keep **`audit-echo-test-1`** / **`hostA-exec-ok-sample`** as supplementary execute proofs, distinct from the OK/BLOCKED/FAILED triple.  
3. Version this file with `Ask_v1.md` / `NoMatch.md` / `Exec_Runtime.md` if evidence lives outside `m-coder`.

See also: [HOST_A_PROOF_PACK_CLOSURE.md](./HOST_A_PROOF_PACK_CLOSURE.md).
