# System Execution Roadmap — End-to-End Flow and Live Progress Tracker

**Entry point:** [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md)

---

## A. End-to-End Flow

```mermaid
flowchart TB
  subgraph L1 [Layer-1: Governance]
    G[Constitution Locked]
    GREG[GREG Protocol]
  end

  subgraph L2 [Layer-2: ML Compilation]
    B[Base Exemplars]
    V[Variants]
    ST[Stability Gate]
    MUT[Stage-6 Mutation]
    FZ[Dataset Freeze]
    SFT[SFT Training]
    PSFT[Post-SFT Revalidation]
  end

  subgraph L3 [Layer-3: Runtime]
    SM[Shadow Mode]
    RV[REF Validator]
    IV[Irreversibility Detector]
    LE[Ledger Emission]
    RL[Runtime Live]
  end

  subgraph L4 [Layer-4: Observation]
    DB[Drift Baseline]
    CV[Collapse Tracking]
    LR[Ledger Reconciliation]
    GA[GREG Audit]
  end

  G --> B
  B --> V --> ST --> MUT --> FZ --> SFT --> PSFT
  PSFT --> SM
  SM --> RV --> IV --> LE --> RL
  RL --> DB --> CV --> LR --> GA
  GA -->|Evidence| GREG
  GREG -->|Pass or Revise| G
```

**Artifact exchange:** Layer-1 provides doctrine and exemplars. Layer-2 consumes doctrine, produces freeze manifest and SFT checkpoint. Layer-3 consumes checkpoint, emits ledger. Layer-4 consumes ledger and baseline, produces drift evidence for GREG.

---

## B. Milestone Table

| Milestone | Layer | Entry | Exit | Failure | Status | Owner | Evidence |
|-----------|-------|-------|------|---------|--------|-------|----------|
| M2.1 Base exemplar completion | L2 | Constitutional lock; GREG readiness | All bases mapped; Phase-3 summary PASS; boundary anchors locked | Bases incomplete; validation fails; boundary mismatch | — | — | — |
| M2.2 Variant stability | L2 | M2.1 complete | Phase-4 variant summary PASS; no softened language; boundary exact | Variants fail stability; phase drift | — | — | — |
| M2.3 Mutation harness v1 | L2 | M2.2 complete | Stage-6A/6B harness runs; ledger populated; taxonomy coverage | Harness crashes; ledger schema invalid; coverage gap | — | — | — |
| M2.4 Collapse vector validation | L2 | M2.3 complete | Stage-6C agent-loop harness passes; collapse vectors classified; pass rate ≥ threshold | Collapse rate exceeds gate; unclassified collapses | — | — | — |
| M2.5 Deterministic dataset freeze | L2 | M2.4 complete | Freeze checklist passes; dataset compiled; manifest locked | Freeze blocked; phase balance fails; dominance coverage gap | — | — | — |
| M2.6 SFT training | L2 | M2.5 complete | Adapter trained; loss stable; structural invariance audit passes | Training divergence; invariance collapse | — | — | — |
| M2.7 Post-SFT mutation revalidation | L2 | M2.6 complete | Post-SFT ledger vs pre-SFT diff acceptable; no rollback criteria | REF collapse; boundary relocation; MIX-to-CONF collapse | — | — | — |
| M3.1 Plan object spec | L3 | M2.7 complete; frozen adapter | Plan object schema defined; authority/irreversibility hooks specified | Spec incomplete; hooks undefined | — | — | — |
| M3.2 Authority validator | L3 | M3.1 complete | Authority checks enforce REF; no bypass paths | Bypass paths; REF not enforced | — | — | — |
| M3.3 Irreversibility detector | L3 | M3.2 complete | Detector blocks at boundaries; Phase-05 CODE semantics honored | Boundary bypass; detector silent | — | — | — |
| M3.4 IDE plugin integration | L3 | M3.3 complete | Plan/Judge/Authority integrated; tool calls gated | Integration incomplete; gates bypassed | — | — | — |
| M3.5 Runtime ledger emission | L3 | M3.4 complete | Ledger rows emitted per run; phase + boundary + allow/block recorded | No emission; missing fields | — | — | — |
| M3.6 Shadow mode validation | L3 | M3.5 complete | Shadow mode runs; ledger captures behavior; no REF violations | REF violations; ledger gaps | — | — | — |
| M4.1 Drift baseline capture | L4 | M3.6 complete | Baseline verdict distribution captured; per-phase, per-surface metrics | Baseline incomplete; missing phases | — | — | — |
| M4.2 Collapse vector live tracking | L4 | M4.1 complete | Collapse vectors tracked in production; probes running | Probes fail; tracking gaps | — | — | — |
| M4.3 Ledger reconciliation dashboard | L4 | M4.2 complete | Pre/post ledgers reconciled; diff visible; anomalies flagged | Reconciliation fails | — | — | — |
| M4.4 GREG audit automation | L4 | M4.3 complete | GREG-trigger automation on drift thresholds; evidence package produced | Automation missing; thresholds wrong | — | — | — |
| M4.5 Constitutional version lock signal | L4 | M4.4 complete | Lock signal emitted when evidence suffices; no drift above threshold | Signal blocked; evidence insufficient | — | — | — |

---

## C. Artifact Matrix

| Artifact | Produced By | Consumed By | Version Pinned | Immutable After |
|----------|-------------|-------------|----------------|-----------------|
| Constitutional manifest | L1 | All layers | GREG ratification | Ratification |
| Golden exemplars | L1 | L2 | GREG lock | Lock |
| Base exemplars | L2 | L2 (variants) | Stage-3 | Freeze |
| Variants | L2 | L2 (mutation) | Stage-4 | Freeze |
| Mutation ledger | L2 | L2 (freeze), L4 | Stage-6C | Ledger final |
| Freeze manifest | L2 | L2 (SFT), L3, L4 | Stage-7 | Freeze |
| SFT checkpoint | L2 | L3 | Stage-8 | Runtime lock |
| Plan object | L3 | L3, L4 | v0.1 | Per request |
| Ledger row | L3 | L4 | v0.1 | Append-only |
| Drift report | L4 | GREG | Per run | — |
| Evidence package | L4 | GREG | Per threshold | — |

---

## D. Critical Risk Zones

- **Pre-freeze gap:** Dataset not frozen; any change to bases/variants invalidates downstream. Mutation harness must pass before freeze.
- **Post-SFT invariance risk:** Training may introduce phase drift, boundary softening, or REF collapse. Post-SFT revalidation is mandatory.
- **Runtime bypass risk:** No REF enforcement at execution; model could act under illegitimacy. Production cannot ship without REF enforcement.
- **Drift detection blind spots:** No production drift baseline; GREG cannot run on live evidence until M4.1 complete.

---

## E. Live Progress Tracker

| Layer | Milestone | Status | % Complete | Evidence Link | Blockers | Next Action |
|-------|-----------|--------|------------|---------------|----------|-------------|
| L1 | Governance lock | Complete | 100 | GREG ratification | — | — |
| L2 | M2.1 Base completion | In Progress | — | — | — | — |
| L2 | M2.2 Variant stability | Not Started | 0 | — | — | — |
| L2 | M2.3 Mutation harness | In Progress | — | Stage-6A/6B | — | — |
| L2 | M2.4 Collapse validation | In Progress | — | Stage-6C | — | — |
| L2 | M2.5 Dataset freeze | Not Started | 0 | — | M2.4 | — |
| L2 | M2.6 SFT training | Not Started | 0 | — | M2.5 | — |
| L2 | M2.7 Post-SFT revalidation | Not Started | 0 | — | M2.6 | — |
| L3 | M3.1 Plan spec | Not Started | 0 | — | M2.7 | — |
| L3 | M3.2–M3.6 Runtime | Not Started | 0 | — | M3.1 | — |
| L4 | M4.1–M4.5 Observation | Not Started | 0 | — | M3.6 | — |

**Status key:** Not Started | In Progress | Complete | Blocked

---

## Definition of Constitutional Completion

**Constitutional completion** is the exact state at which:

1. **Layer-2 is formally closed:** Freeze manifest locked; SFT training complete; post-SFT revalidation passed; no rollback criteria triggered; adapter and dataset immutable.

2. **Layer-3 is SAFE:** REF enforced; irreversibility detector blocks at boundaries; ledger emits phase + boundary + allow/block per run; Phase-05 CODE semantics honored; shadow mode validated; no bypass paths.

3. **Layer-4 immune system active:** Drift baseline captured; collapse vectors tracked in production; ledger reconciliation operational; GREG-trigger automation runs on thresholds; lock signal emitted when evidence suffices.

4. **System eligible for production lock:** All milestones M2.1–M2.7, M3.1–M3.6, M4.1–M4.5 complete; GREG has admissible evidence; no drift above threshold; constitutional version lock signal emitted.

At constitutional completion, the system may proceed to production deployment with continuous drift monitoring and GREG-triggered governance review on threshold violation.
