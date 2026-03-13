# System Dependency Supply Chain Audit

**Report date:** 2026-03-13  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## Scope

Inspect dependency manifests, container image references, plugin build files, and ML-related artifact configs. Verify dependencies are pinned where appropriate and no unsafe install patterns (e.g. unpinned installs, curl-pipe execution) exist that could compromise supply-chain or build reproducibility.

---

## Surfaces Inspected

- **Python:** `runtime/rag/requirements.txt`, `ml/training/requirements.txt`, `ml/training/pipeline/stage6/pyproject.toml`
- **Plugin:** `jetbrains-plugin/build.gradle.kts` (dependencies block, repositories)
- **Container:** `runtime/sandbox/container_sandbox_driver.py` (image and runtime references)
- **Artifacts:** `ml/training/artifacts/artifact_store.yaml` (backend, env-based secrets)
- **Scripts:** No `curl | bash` or `pip install` from git URL in inspected CI/scripts

---

## Findings

### Python dependency manifests

| File | Pinning | Notes |
|------|---------|--------|
| `runtime/rag/requirements.txt` | Minimum versions only (`>=`) | fastapi>=0.104.0, torch>=2.0.0, etc. No exact pins; installs can drift across runs. |
| `ml/training/requirements.txt` | Minimum versions only (`>=`) | transformers>=4.35.0, torch>=2.0.0, etc. Same as above. |
| `ml/training/pipeline/stage6/pyproject.toml` | No version deps in `dependencies = []` | Optional `yaml = ["pyyaml"]`; build-system setuptools>=61. Minimal surface. |

**Observation:** No exact version pins (e.g. `==`) in the two requirements files. Reproducibility depends on environment or lockfiles not present in the audited tree.

### Plugin build (Gradle)

- **jetbrains-plugin/build.gradle.kts:** Repositories: mavenCentral() only. Dependencies use explicit versions: gson:2.10.1, mockito-core:5.11.0, mockito-kotlin:5.2.1, junit-jupiter:5.10.2. IntelliJ version 2023.3. **Finding:** Versions are pinned; no dynamic or snapshot versions observed.

### Container references

- **runtime/sandbox/container_sandbox_driver.py:** `DEFAULT_IMAGE = "python:3.12-slim"`. No digest or version tag (e.g. `@sha256:...`). **Finding:** Image is not pinned; `python:3.12-slim` can change over time.

### Artifact store config

- **ml/training/artifacts/artifact_store.yaml:** Backend `local` with `root` path; S3 optional with credentials via env vars (`ARTIFACTS_S3_ACCESS_KEY_ID`, etc.). No inline secrets. **Finding:** Credentials not in file; env-based pattern is acceptable.

### Unsafe install patterns

- Grep/inspection did not find `curl | bash`, `wget -qO- | sh`, or `pip install <git URL>` in CI scripts or root-level install docs under the audited paths. CI scripts in `scripts/ci/` are structural guards (e.g. check_structure, check_no_governance_yaml_in_docs); they do not install dependencies.

---

## Risks

1. **Unpinned Python deps:** `requirements.txt` files use only lower bounds. Builds at different times can pull different transitive versions; supply-chain and reproducibility risk if a dependency is compromised or behavior changes.
2. **Unpinned container image:** `python:3.12-slim` can be overwritten by registry; no digest pin. Minor risk for container-based sandbox reproducibility and supply chain.
3. **Single repository (Maven Central) for plugin:** No finding of alternate repos; if a dependency were only available elsewhere, build could be modified to add repos (out of scope for this audit).

---

## Verdict

**PASS WITH CAVEAT.** Dependency and build surfaces inspected; no unsafe install patterns (curl-pipe, unpinned git installs) found. Plugin dependencies are pinned. Python requirements use minimum versions only (not pinned); container default image is not digest-pinned. Recommend pinning critical Python deps or introducing lockfiles and pinning container image by digest for stronger supply-chain and reproducibility; not required for audit pass. No modifications were made.
