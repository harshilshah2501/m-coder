# Reasoning synthesis shadow — decision review

**Source:** `docs/validation/REASONING_SYNTHESIS_SHADOW_REPORT.md` (baseline run, 2026-05-01 05:16 UTC, 16 scenarios).  
**Scope:** Compare legacy `articulated_answer` / stub debug text vs `metadata.reasoning_synthesis` **without** Phase D narration wiring.

---

## Aggregate metrics (baseline table)

| Metric | Value |
|--------|------:|
| Scenarios | 16 |
| `method_collapse_risk.detected` true (synthesis) | 0 |
| `method_collapse_detected` true (rubric: synthesis ∪ legacy heuristic) | 0 |
| `overclaim_risk` = 1 | 16 |
| `overclaim_risk` ≥ 2 | 0 |
| depth_score average (Ask rows 1–9 only) | ≈ 1.67 |
| depth_score average (all 16) | ≈ 1.56 |
| fluency_score | 2 on all rows |
| grounding_score | 2 on all rows |

*Rubric is heuristic; debug rows 10–16 use stub Explain/Debug text, so fluency/depth are not comparable to real debug.*

---

## Where synthesis is **stronger** than legacy (for Phase D)

| Signal | Why |
|--------|-----|
| **Subsystem label + `system_summary`** | Legacy often collapses to thin disclaimers (e.g. Ask 2–4, 7: “insufficient… snapshot”) while synthesis still assigns `mail_configuration` / `config_store` / `api_layer` and fills **proven_facts** from route/EventBus maps when present. |
| **Multi-component breadth** | Ask 5 & 8: legacy stays readable but **synthesis** can surface `distinct_grounded_components` = 5 and depth_score = 3 with structured buckets — better substrate for “engineer-like” opening sentences later. |
| **Explicit collapse signal** | `method_collapse_risk` gives a **machine-checkable** guardrail before prose; legacy alone does not expose that. |

---

## Where synthesis is **weaker** or **not yet better** than legacy

| Signal | Why |
|--------|-----|
| **Thin evidence rows** | Ask 2–4, 7: legacy correctly hedges; synthesis subsystem guess may look “confident” in label while **distinct = 1** — narrative must still lean on `confidence_limits` (Phase D contract). |
| **Structural / inheritance** | Ask 1 & 6: legacy already delivers strong AbstractAPI messaging; synthesis must **not** replace that prose blindly — merge `system_summary` with existing structural branch in `articulated_answer`. |
| **Debug rows** | Stub debug text makes rubric meaningless for 10–16; judge Debug later with real `explain_debug` + separate synthesis cues only. |

---

## Hallucination / trust posture (baseline)

- **Synthesis:** bounded to `reasoning_context` only; **no novel classes** in schema. Risk is **misleading taxonomy** (subsystem label) or **over-trust** in maps — mitigated by `proven_facts` vs `bounded_inferences` separation.
- **Legacy:** can read fluent but still **anchor-heavy**; rubric `method_collapse_detected` stayed false on this run.

---

## Top 5 fixes **before** Ask consumption (Phase D)

1. **Gate `system_summary` when `distinct_grounded_components` &lt; 2** — prepend coverage limits or shorten subsystem confidence (avoid sounding definitive on one-class snapshots).
2. **Align subsystem classifier with `_query_intent`** where Ask already has special cases (e.g. structural AbstractAPI) so Phase D does not fight `_unified_paragraphs`.
3. **Preserve structural-query fast path** in `articulated_answer` when flag is on — synthesis augments, does not replace inheritance answers.
4. **Add extended shadow + adversarial list** — validate taxonomy under vague/misleading prompts (`REASONING_SYNTHESIS_EXTENDED_SHADOW_REPORT.md`).
5. **Define flag rollout**: `MCODER_REASONING_SYNTHESIS_V1=1` only after extended report shows **no regression** on collapse/overclaim histograms vs baseline.

---

## Go / no-go sketch for Phase D

| Check | Baseline status |
|-------|-----------------|
| Ask 9/9 scenarios pass (legacy default) | Assume green — re-run after any synthesis wiring |
| Synthesis metadata present & validates | Yes (`reasoning_synthesis.v1`) |
| Extended adversarial run reviewed | Pending — run extended shadow generator |
| Debug left untouched | Yes — do not mix Phase D with debug payload work |

---

## Extended run (`REASONING_SYNTHESIS_EXTENDED_SHADOW_REPORT.md`)

After synthesis tuning (`_expand_grounded_classes`, richer flow steps, rubric depth tied to proven facts): regenerate with `--extended`.

Latest generator output (36 rows = 9 Ask + 20 adversarial + 7 Debug):

| Metric | Value |
|--------|------:|
| `method_collapse_risk.detected` true | 0 |
| Rubric `method_collapse_detected` true | 0 |
| Avg depth / fluency / grounding | **~3.00** / 2.00 / 2.00 |
| `overclaim_risk` | all **1** (`{1: 36}`) |

**Read-through:** Depth rises from map/collaborator/EventBus **expansion** (same evidence bundle); overclaim stays low because **`proven_facts`** remain route/topology-backed. Review extended table before **`MCODER_REASONING_SYNTHESIS_V1`** Phase D.

---

## Regenerate reports

Standard (16-row):

```bash
PYTHONPATH=. python3 runtime/scripts/gen_reasoning_synthesis_shadow_report.py
```

Extended (Ask + adversarial + Debug):

```bash
PYTHONPATH=. python3 runtime/scripts/gen_reasoning_synthesis_shadow_report.py --extended
```
