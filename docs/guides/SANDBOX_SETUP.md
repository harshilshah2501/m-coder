# Motadata Sandbox - Setup Complete ✅

**Date:** December 17, 2025  
**Status:** Operational  
**Purpose:** Executable Java 17 + Maven + Vert.x environment for Motadata-Bench task verification

---

## What Was Built

### 1. Docker Infrastructure
- **Location:** `rag-system/docker/motadata-sandbox/`
- **Image:** `rag-system_motadata-sandbox`
- **Base:** Eclipse Temurin JDK 17 (official OpenJDK distribution)

### 2. Pre-cached Dependencies
Dependencies pre-installed during image build (speeds up task execution):
- **Vert.x 4.3.4** (Core, Web, Config)
- **Jackson 2.15.2** (JSON processing)
- **SLF4J 2.0.7** (Logging)
- **JUnit 4.13.2 + Vert.x Unit** (Testing)

### 3. Integration with docker-compose
- **Service name:** `motadata-sandbox`
- **Volumes:**
  - `/tmp/motadata-workspace:/workspace` - Task execution mount point
  - `maven-cache` - Persistent dependency cache (shared across runs)
- **Network:** `motadata-rag-network` (shared with Qdrant + Neo4j)

### 4. Verification Test Suite
**Test Project:** `docker/motadata-sandbox/test-project/`

✅ **Verification Results:**
```
Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
```

**Tests Validated:**
1. ✅ Java 17 compilation
2. ✅ Vert.x deployment and async patterns (`vertx.setPeriodic`)
3. ✅ HTTP server creation and health endpoint
4. ✅ JUnit + Vert.x Unit test execution

---

## How to Use

### Start All Services
```bash
cd rag-system/
docker-compose up -d
```

### Run Sandbox Verification
```bash
cd rag-system/
./verify_sandbox.sh
```

### Execute Code in Sandbox (Manual)
```bash
# Mount your Java project to /workspace
docker run --rm \
  -v /path/to/java/project:/workspace \
  -v maven-cache:/root/.m2/repository \
  rag-system_motadata-sandbox \
  bash -c "cd /workspace && mvn clean compile test"
```

### Spawn Sandbox for Task Execution (Programmatic)
```python
# Future task_executor.py will use this pattern
subprocess.run([
    "docker", "run", "--rm",
    "-v", f"{task_workspace}:/workspace",
    "-v", "maven-cache:/root/.m2/repository",
    "rag-system_motadata-sandbox",
    "bash", "-c", "cd /workspace && mvn compile"
])
```

---

## Next Steps (Motadata-Bench Integration)

### Phase 2: Define 5 Tasks ⏭️
Create `evaluation/motadata_tasks/` with Harbor format tasks:
```yaml
task_id: netapp_monitor_plugin
prompt: "Create a NetApp Storage Monitor plugin with SNMP polling"
start_state: commit_abc123
verifier_script: |
  mvn test -Dtest=NetAppMonitorTest
```

### Phase 3: Build Task Executor ⏭️
Create `evaluation/task_executor.py`:
- Spawn sandbox container
- Mount AI-generated code
- Run verifier script
- Capture Pass/Fail + logs

### Phase 4: Generate Training Data ⏭️
- Run Iter9 baseline (expect 0-20% pass)
- Manually fix failures in same environment
- Save `{task_id, model_attempt, human_solution}` pairs
- Train Iter10 on verified behavior

---

## Architecture Decisions

### Why Eclipse Temurin?
- Official OpenJDK builds (replaces Oracle JDK)
- LTS support for Java 17
- Widely adopted in production

### Why Vert.x 4.3.4?
- Matches Motadata production architecture (async event-driven)
- Training data shows heavy `vertx.setPeriodic` / `EventBus` usage
- Anti-pattern detection (e.g., `Thread.sleep` in verticles)

### Why Persistent Maven Cache?
- Docker volume `maven-cache` survives container restarts
- First run: ~20 seconds to download dependencies
- Subsequent runs: <2 seconds (dependencies cached)
- Critical for rapid task iteration in Phase 3/4

### Why No Motadata Source Code in Image?
- Sandbox is **generic** - works with any Java 17 + Maven project
- Actual Motadata code mounted at runtime via `/workspace`
- Avoids coupling image build to proprietary code changes

---

## Files Created

```
rag-system/
├── docker/
│   └── motadata-sandbox/
│       ├── Dockerfile              # JDK 17 + Maven + Vert.x
│       ├── entrypoint.sh           # Initialization script
│       ├── .dockerignore           # Build context exclusions
│       └── test-project/           # Verification test suite
│           ├── pom.xml
│           ├── src/main/java/.../SampleVerticle.java
│           └── src/test/java/.../SandboxVerificationTest.java
├── docker-compose.yml              # ✏️ Updated with motadata-sandbox service
└── verify_sandbox.sh               # Build + test automation script
```

---

## Troubleshooting

### "Permission denied" on cleanup
**Cause:** Docker runs as root, creates files owned by root  
**Fix:** Script now uses `sudo rm` for cleanup (or ignores errors)

### "Cannot find image rag-system_motadata-sandbox"
**Cause:** Image name mismatch  
**Fix:** Use `docker-compose build motadata-sandbox` (not `docker build`)

### Tests fail with "Cannot find symbol"
**Cause:** Missing Maven dependencies  
**Fix:** Check `pom.xml` has correct `groupId:artifactId:version`  
**Verify:** Run `mvn dependency:tree` inside container

---

## Performance Metrics

**Image Build Time:** ~2 minutes (first time)  
**Dependency Cache:** ~90 packages (175 MB)  
**Compile Time:** <2 seconds (cached dependencies)  
**Test Execution:** ~1.6 seconds (3 Vert.x tests)  

**Total Verification Time:** <10 seconds after initial build

---

## Success Criteria ✅

- [x] Docker image builds successfully
- [x] Java 17 compilation works
- [x] Maven test execution works
- [x] Vert.x dependencies resolved
- [x] Integration with docker-compose network
- [x] Persistent Maven cache configured
- [x] Verification script automated

**Status:** ✅ **Phase 1 Complete - Ready for Phase 2 (Task Definition)**
