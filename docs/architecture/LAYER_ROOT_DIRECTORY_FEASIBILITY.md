# Feasibility: layer-prefixed root directories (`L1-governance`, `L2-ml`, …)

**Question:** Should the repository use root folder names like `L1-governance/`, `L2-ml/`, `L3-runtime/`, `L4-observation/` instead of `governance/`, `ml/`, `runtime/`, `observation/`?

**Short answer:** **Not recommended as a spontaneous reshuffle.** It is **possible** only as a **planned, migration-only** effort (dedicated branch, mechanical rename, full CI green). It is **not** something to mix with feature work.

## Why it is costly

1. **Python package paths** — Imports are pervasive: `runtime.*`, `governance.*`, `ml.*`, `observation.*`, tests, packaging (`motadata-context-layer`), scripts, and IDE/plugin references. A rename touches **thousands** of paths, not tens.
2. **Cross-layer roots** — `jetbrains-plugin/`, `packaging/`, `validation/`, `docs/`, `archive/` do not belong to a single layer; a layer-only layout does not “neaten” them without a second naming scheme.
3. **Tooling** — Gradle, Docker, GitHub Actions, CodeRabbit paths, local runbooks, and operator muscle memory all key off current names.
4. **Redundancy** — Layer semantics are already **canonical in documentation** ([`ARCHITECTURE_4_LAYER.md`](../ARCHITECTURE_4_LAYER.md), [`MASTER_SYSTEM_SPEC.md`](../MASTER_SYSTEM_SPEC.md)). Renaming directories **duplicates** that signal in the filesystem without changing runtime behavior.

## Lower-risk alternatives

- **Keep current directory names**; use **REPO_LAYOUT_INVENTORY** and architecture docs as the map.
- **Optional:** a single **root `README` table** or `docs/audit/REPO_LAYOUT_INVENTORY.md` as the enumerated “L1–L4 + satellite” view (already aligned with layers conceptually).

## If you still want physical renames later

Use a **migration checklist**: freeze mainline, branch, run a **codemod** (imports + string paths), update CI, run full `pytest`, update packaging and plugin paths, then merge as **rename-only** PR with no feature changes.

---

**Related:** [`docs/audit/RUNTIME_REORG_CANDIDATES.md`](../audit/RUNTIME_REORG_CANDIDATES.md) — defers mass tree moves by design.
