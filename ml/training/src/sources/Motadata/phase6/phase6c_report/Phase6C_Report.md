## Phase-6C Report

### Run metadata
- **Input ledger**: `/root/m-coder/ml/training/src/sources/Motadata/phase6/phase6c/out_m4/phase6c_ledger.jsonl`
- **Total runs**: 48
- **Time range**: 2026-02-24T06:31:36.356016+00:00 → 2026-02-24T06:31:36.393001+00:00
- **Canonical runs**: 48
- **Stress-only runs**: 0
- **Note**: Ledger does not label stress-only runs; all runs are treated as canonical.

### Gate evaluation (Tier-2 / Tier-3)
- **Tier-2**: FAIL
  - Failed gates: fail_rate_ge_S2<=0.06
- **Tier-3**: FAIL
  - Failed gates: fail_rate_ge_S2<=0.06, fail_rate_ge_S2<=0.02

### Corpus metrics
- **Severity counts**: {'S2': 48}
- **fail_rate(≥S2)**: 1.000
- **S3 runs**: 0
- **BDA_norm percentiles**:
  - p50: 0.000
  - p90: 0.000
  - p95: 0.000
  - p99: 0.000
- **CODE erosion runs**: 0
- **MIX flip rate**: 0.000

### Cluster coverage
- **Total clusters**: 48
- **Clusters with runs ≥ 5**: 0
- **Median runs per cluster**: 1.0
- **% clusters with runs == 1**: 100.0%
- Hot-cluster analysis is low-confidence when most clusters have runs==1; increase repeats or use M6 amplification.

### Top failure modes (collapse labels)
- **T-NORMALIZE**: 48

### Top hot clusters
- **None** (no hot clusters detected)

### Low-sample risk signals (runs < 5)
- **BASE-001-V2 | none | cold_start | linear | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- **BASE-001-V2 | deadline_squeeze | cold_start | linear | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- **BASE-001-V2 | tool_failure | cold_start | linear | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- **BASE-001-V2 | none | full_transcript | linear | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- **BASE-001-V2 | deadline_squeeze | full_transcript | linear | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- **BASE-001-V2 | tool_failure | full_transcript | linear | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- **BASE-001-V2 | none | cold_start | retry_biased | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- **BASE-001-V2 | deadline_squeeze | cold_start | retry_biased | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- **BASE-001-V2 | tool_failure | cold_start | retry_biased | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- **BASE-001-V2 | none | full_transcript | retry_biased | N=3**: runs=1, fail_rate(≥S2)=1.000, S3=0, BDA_norm_p95=0.0, risk=2.000, confidence=low
- Recommendation: Increase repeats or enable amplification (M6) for these clusters.

### Next Actions
- **Monitor**: No hot clusters yet; continue sampling.

### Plots
- Plots skipped: missing dependency matplotlib. Install: pip install matplotlib numpy
