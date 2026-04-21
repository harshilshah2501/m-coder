# Motadata product repository — source tree snapshot

**Generated:** 2026-04-21 (filesystem scan)  
**Source path:** `/home/harshil/Projects/Motadata`  
**Purpose:** Orientation for Context Layer indexing, authority registry alignment, and verification (`--workspace-root`). This is **not** a substitute for Gradle/module docs inside the Motadata repo; regenerate when the product layout changes.

**Lineage:** A mirror sync recorded `git_commit` **`078d2df1422751e321c350600b25a024b650bc45`** in `motadata_snapshot.json` at the repo root (same path). Re-run the commands below after pulling Motadata to refresh this document.

**Stats (this checkout):**

| Scope | Count |
| ----- | ----- |
| `*.java` under `motadata/src/main/java` | 519 |

---

## Repository root

```
/home/harshil/Projects/Motadata/
├── .git/
├── .idea/
├── motadata/                 ← Maven module (primary Java tree)
└── motadata_snapshot.json    ← optional mirror metadata (rsync tooling)
```

All product sources for indexing and Layer-5 live under **`motadata/`**.

---

## `motadata/` module (top level)

Maven project (`pom.xml`). Representative layout:

```
motadata/
├── config/
├── db-files/               ← bundled DB assets (widgets, templates, SNMP, …)
├── fonts/
├── indices/
├── plugin-scripts/
│   ├── plugins/
│   └── trace/
├── src/
│   ├── main/
│   │   ├── java/           ← com.mindarray.* (see below)
│   │   └── resources/
│   └── test/
│       ├── java/           ← additional test-only packages (may differ from main)
│       └── resources/
├── target/                 ← build output (exclude from “source structure”)
├── test-plugin-metrics/
└── uploads/
```

### `db-files/` (depth 2)

```
db-files/
├── dashboard-widgets/
├── email-templates/
├── icons/
├── metric-descriptions/
├── report-templates/
│   ├── css/
│   └── js/
├── reports/
├── snmp-templates/
├── snmp-templates-profiles/
├── snmp-trap-profiles/
└── template-widgets/
```

---

## Java package tree — `com.mindarray` (main sources)

Root namespace: `motadata/src/main/java/com/mindarray/`.

**Top-level packages (directories):**

| Package | Role (high level) |
| ------- | ----------------- |
| `agent` | Agent runtime / metrics |
| `aiops` | AIOps correlation, dependency processing, constants |
| `api` | REST API routers, `AbstractAPI`, domain “API” verticles |
| `cache` | Config/policy/availability caches |
| `compliance` | Compliance rules and engine |
| `config` | Configuration management |
| `datastore` | Persistence / datastore facades |
| `db` | DB services, config DB |
| `eventbus` | Local/remote event transport, NSQ, ZMQ, TCP/UDP |
| `flow` | Flow / IP / geolocation mapping |
| `ha` | High availability |
| `integration` | Integrations |
| `job` | Scheduled / job processing |
| `log` | Logging utilities |
| `manager` | Manager-side bootstrap and lifecycle |
| `netroute` | Network routing |
| `nms` | Network management |
| `notification` | Notifications |
| `patch` | Patching |
| `plugin` | Plugin host |
| `policy` | Policies |
| `report` | Reporting |
| `rum` | Real user monitoring |
| `runbook` | Runbooks |
| `slo` | SLO |
| `store` | Store abstractions |
| `streaming` | Streaming |
| `trace` | Tracing |
| `util` | Utilities |
| `visualization` | Visualization |

Bootstrap and shared entry classes sit **directly** under `com.mindarray` (e.g. `Bootstrap*.java`, `GlobalConstants.java`, `ErrorCodes.java`).

**Directory tree (packages only, depth 3):**

```
com/mindarray
├── agent
├── aiops
├── api
├── cache
├── compliance
├── config
├── datastore
├── db
├── eventbus
├── flow
├── ha
├── integration
├── job
├── log
├── manager
├── netroute
├── nms
├── notification
├── patch
├── plugin
├── policy
├── report
├── rum
├── runbook
├── slo
├── store
├── streaming
├── trace
├── util
└── visualization
```

Layer-5 **authority** paths in m-coder (`runtime/layer5/authority/product_authority_registry.yaml`) use paths relative to this module, e.g. `src/main/java/com/mindarray/aiops/...`.

---

## Test sources (`src/test/java`)

Test tree includes packages that may not mirror `main` one-to-one (e.g. `poller`, `discovery`, `provision`, `topology`, `suite`). Use for **tests** only; indexing and verification normally target **`src/main/java`**.

---

## Regenerating this snapshot

From a machine that has the Motadata checkout and `tree`:

```bash
MOTADATA_ROOT="/home/harshil/Projects/Motadata"
tree -L 4 -d --noreport "$MOTADATA_ROOT/motadata"
tree -d -L 3 --noreport "$MOTADATA_ROOT/motadata/src/main/java/com/mindarray"
find "$MOTADATA_ROOT/motadata/src/main/java" -type f -name '*.java' | wc -l
```

Update the header (date, path, counts, optional `git rev-parse HEAD` from `Motadata/.git`) when you commit a refreshed doc.
