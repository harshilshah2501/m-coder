# Layer-II Irreversible Surface Discovery Report

**Mode:** Layer-II Irreversible Surface Discovery  
**Scope:** Motadata codebase (documented artifacts under `ml/training/src/sources/Motadata`)  
**Exclusion:** Boundaries already mapped in BASE-001 through BASE-017  
**Classification:** None (no phase assignment, no new BASE IDs proposed)

---

## Step 1 — Candidate Search Summary

Searched for: `update*`, `write*`, `persist*`, `save*`, `delete*`, `add*`, `remove*`, `eventBus().send`, `eventBus().request`, `route(`, external API calls, scheduler completion signals.  
Filtered to: mutate persistent state, publish irreversible events, trigger external execution, modify configuration, or change object lifecycle state.

## Step 2 — Exclusions Applied

The following were treated as already mapped and excluded from this list:

- `result.put(SEVERITY, ...)` + `processPolicyFlap()` + `triggerAction()` + `EVENT_NOTIFICATION` (BASE-001, 007, 009, 010)
- `ObjectStatusCacheStore.getStore().updateItem(...)` in AvailabilityCorrelationEngine (BASE-002, 008)
- `vertx.fileSystem().writeFileBlocking(...)` correlation config line 443 in AvailabilityCorrelationEngine (BASE-011)
- `suppressedPolicies.get(objectId).add(...)` (BASE-003)
- `Bootstrap.vertx().eventBus().send(EVENT_RUNBOOK, ...)` PolicyEngineConstants 1403 (BASE-004)
- `eventBus().request(EVENT_NOTIFICATION, ...)` PolicyEngineConstants 1259, 1288; `Notification.send()` 1375 (BASE-006)
- `triggerAction(severity, trigger, policy, context, ...)` 1135 (BASE-007)
- `discard(event, key, ..., STATUS_FAIL/STATUS_ABORT)` → updateItem 813, reply 828 (BASE-008)
- EventPolicyInspector `eventBus().send(EVENT_RUNBOOK, ...)` 1285; UIActionEventHandler EVENT_RUNBOOK send/request; RunbookEngine `route()`, `writeFileBlocking` worklog/config, `EVENT_SCHEDULER_COMPLETE` (BASE-013)
- RunbookEngine `qualify()` / prevention of `route()` (BASE-014)
- `MetricPolicyCacheStore.getItemsBySeverity`, `MetricCacheStore.getMetricPollTimestamps`, `ObjectConfigStore.getItemsByGroup` (BASE-015, 016, 017 — read boundaries)

---

## Step 3 — Structured Discovery List

Candidates below are **not** duplicates of BASE-001..017. For each: File, Method, Exact irreversible call, State mutated, Authorization check present?, Ambiguity present?, Multi-pressure context present?

---

### 1. Integration event dispatch (policy-triggered)

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` |
| **Method** | `triggerAction` (integration branch) |
| **Exact irreversible call** | `Bootstrap.vertx().eventBus().send(EventBusConstants.EVENT_INTEGRATION, integrationContext)` (L1424; context merge L3412) |
| **State mutated** | External ticketing/monitoring systems (ServiceNow, Jira, LAMA, etc.); downstream integration state |
| **Authorization check exists** | No (no user/principal or getItemsByUserProfile in method; policy/context/entityId only) |
| **Ambiguity exists** | Possible (which integration, retry semantics, idempotency) |
| **Multi-pressure context exists** | Yes (policy automation + integration delivery pressure) |

---

### 2. Notification dispatch from NetRoute policy inspector

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/policy/NetRoutePolicyInspector.java` |
| **Method** | Notification path handlers |
| **Exact irreversible call** | `vertx.eventBus().request(EventBusConstants.EVENT_NOTIFICATION, ...)` (L758, 796, 905, 935) |
| **State mutated** | External notification delivery (email/SMS/Teams/Slack); cannot un-send |
| **Authorization check exists** | No (no getItemsByUserProfile or user check in dispatch path per AUTHORITY_SURFACE_SCAN) |
| **Ambiguity exists** | Same class as BASE-006 (recipient/access/channel) but distinct artifact |
| **Multi-pressure context exists** | Possible (net-route policy vs. recipient filtering) |

---

### 3. Notification dispatch from Event policy inspector

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/policy/EventPolicyInspector.java` |
| **Method** | triggerAction / notification caller |
| **Exact irreversible call** | `vertx.eventBus().request(EventBusConstants.EVENT_NOTIFICATION, ...)` (L1152, 1191) |
| **State mutated** | External notification delivery |
| **Authorization check exists** | No (no getItemsByUserProfile in dispatch path) |
| **Ambiguity exists** | Same as BASE-006 type; distinct inspector origin |
| **Multi-pressure context exists** | Possible (event policy vs. metric policy trigger paths) |

---

### 4. Policy trigger state persistence (MetricPolicyCacheStore)

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` (caller); `motadata/src/main/java/com/mindarray/store/MetricPolicyCacheStore.java` (store) |
| **Method** | Downstream of `processPolicyFlap()` / trigger path |
| **Exact irreversible call** | `MetricPolicyCacheStore.getStore().updateItem(...)` (L1017) |
| **State mutated** | Policy trigger state; UI alert visibility; severity counts; alert widget state |
| **Authorization check exists** | No (policy cache stores by object id; no user check in store — AUTHORITY_LEAK_TRACE_FINDINGS) |
| **Ambiguity exists** | Possible (policy key by object vs. user scope) |
| **Multi-pressure context exists** | Yes (flap detection, re-notification timers, UI visibility) |

---

### 5. Policy cache store persistence to disk

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/store/MetricPolicyCacheStore.java` |
| **Method** | Persist path |
| **Exact irreversible call** | `vertx.executeBlocking(promise -> { ... writeFileBlocking(path, ...) })` (L899–903) |
| **State mutated** | Persistent policy cache on disk; recovery state |
| **Authorization check exists** | N/A (internal store persistence) |
| **Ambiguity exists** | Possible (dirty vs. write ordering; concurrent writes) |
| **Multi-pressure context exists** | Possible (multiple writers to same store) |

---

### 6. Object status cache store persistence to disk

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/store/ObjectStatusCacheStore.java` |
| **Method** | Persist path |
| **Exact irreversible call** | `vertx.executeBlocking(result -> { ... writeFileBlocking(path, ...) })` (L507–511) |
| **State mutated** | Persistent object status cache; recovery state |
| **Authorization check exists** | N/A (internal store persistence) |
| **Ambiguity exists** | Possible (dirty vs. write ordering) |
| **Multi-pressure context exists** | Yes (correlation engine + other writers; BASE-002/008 use updateItem) |

---

### 7. Log pattern cache store persistence

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/store/LogPatternCacheStore.java` |
| **Method** | Persist path |
| **Exact irreversible call** | `vertx.executeBlocking(promise -> { ... writeFileBlocking(path, ...) })` (L323–327) |
| **State mutated** | Persistent log pattern cache on disk |
| **Authorization check exists** | N/A (internal) |
| **Ambiguity exists** | Unclear |
| **Multi-pressure context exists** | Unclear |

---

### 8. Net route cache store persistence

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/store/NetRouteCacheStore.java` |
| **Method** | Persist path (two blocks) |
| **Exact irreversible call** | `vertx.executeBlocking(...)` with `writeFileBlocking` inside (L264–268, L284–288) |
| **State mutated** | Persistent net route cache on disk |
| **Authorization check exists** | N/A (internal) |
| **Ambiguity exists** | Unclear |
| **Multi-pressure context exists** | Unclear |

---

### 9. RUM policy cache store persistence

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/store/RUMPolicyCacheStore.java` |
| **Method** | Persist path; dirty flag |
| **Exact irreversible call** | `vertx.executeBlocking(promise -> { ... writeFileBlocking(path, ...) })` (L740–744); dirty()/setDirty (L714–716) |
| **State mutated** | Persistent RUM policy cache; dirty state |
| **Authorization check exists** | N/A (internal) |
| **Ambiguity exists** | Possible (dirty vs. write ordering) |
| **Multi-pressure context exists** | Possible (dirty flag shared) |

---

### 10. Trap cache update and dump

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/store/TrapCacheStore.java` |
| **Method** | `updateItem`; `dump()` |
| **Exact irreversible call** | `updateItem(trapId, value)` (L106–120); `dump()` → `dirty.set(true)`; `writeFileBlocking(path, ...)` (L129–137) |
| **State mutated** | In-memory trap cache; persistent trap dump file |
| **Authorization check exists** | N/A (internal store) |
| **Ambiguity exists** | Possible (updated vs. dirty non-atomic; MIX_CODE_SURFACE_EXTRACTION) |
| **Multi-pressure context exists** | Yes (updateItem callers + dump; concurrency) |

---

### 11. Widget config store update (visualization)

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/visualization/VisualizationCacheEngine.java` |
| **Method** | Handler (widget update path) |
| **Exact irreversible call** | `WidgetConfigStore.getStore().getItem(...)` then `update(WidgetConfigStore.getStore().getItem(...), true)` (L282, 378, 471, 504) |
| **State mutated** | Widget configuration; visualization session state |
| **Authorization check exists** | Unclear (upstream uses getItemsByUserProfile in some visualization paths; this handler uses getStore().getItems() at L347 without user filter per AUTHORITY_SURFACE_SCAN) |
| **Ambiguity exists** | Possible (session vs. widget scope; merge semantics) |
| **Multi-pressure context exists** | Yes (eventBus send/publish, getStore().getItem, update; MIX_CODE_SURFACE_EXTRACTION) |

---

### 12. Action event logging (triggered actions)

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` (or caller of writeTriggeredActionEvent) |
| **Method** | Call sites of `writeTriggeredActionEvent()` |
| **Exact irreversible call** | `writeTriggeredActionEvent()` (persists notification/runbook execution events) |
| **State mutated** | Persistent action/audit log; compliance and correlation history |
| **Authorization check exists** | No (no explicit authority check at write site in docs) |
| **Ambiguity exists** | Possible (what to log; retention) |
| **Multi-pressure context exists** | Yes (trigger path + audit requirement) |

---

### 13. UI policy notification publication

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/policy/SeverityChangeEventProcessor.java` |
| **Method** | Handler (notification path) |
| **Exact irreversible call** | `EventBusConstants.publish(..., EventBusConstants.EVENT_POLICY_NOTIFICATION, ...)` (L258) |
| **State mutated** | Real-time UI state; user notification popups; alert counts |
| **Authorization check exists** | Yes (upstream: `filterNotifications(..., getObjectIdsByUserProfile(userId))` at L219) |
| **Ambiguity exists** | Possible (recipient vs. severity vs. channel) |
| **Multi-pressure context exists** | Yes (severity change + UI visibility + access filtering) |

---

### 14. Shutdown util file write

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/util/ShutdownUtil.java` |
| **Method** | (method performing shutdown write) |
| **Exact irreversible call** | `vertx.fileSystem().writeFileBlocking(PATH, ...)` (L259) |
| **State mutated** | File system (shutdown state/path) |
| **Authorization check exists** | No (no user/permission check in same method) |
| **Ambiguity exists** | Low |
| **Multi-pressure context exists** | No |

---

### 15. Diagnostic util file writes

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/util/DiagnosticUtil.java` |
| **Method** | Diagnostic write methods |
| **Exact irreversible call** | `writeFileBlocking(...engine-stats.json, ...)`, `writeFileBlocking(...faulty-objects.json, ...)` (L65, 162) |
| **State mutated** | Diagnostic files on disk |
| **Authorization check exists** | No |
| **Ambiguity exists** | Low |
| **Multi-pressure context exists** | No |

---

### 16. Log util config file writes

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/util/LogUtil.java` |
| **Method** | (method writing log config) |
| **Exact irreversible call** | `writeFileBlocking(...agent.json, ...)`, `writeFileBlocking(...motadata.json, ...)` (L247, 262) |
| **State mutated** | Log configuration files |
| **Authorization check exists** | No |
| **Ambiguity exists** | Low |
| **Multi-pressure context exists** | No |

---

### 17. License util persistence

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/util/LicenseUtil.java` |
| **Method** | License write methods |
| **Exact irreversible call** | `writeFileBlocking(LICENSE_PATH, ...)`, `writeFileBlocking(LICENSE_FILE, ...)` (L380, 624, 863) |
| **State mutated** | License state on disk; product entitlement |
| **Authorization check exists** | No (no authority check in same method) |
| **Ambiguity exists** | Possible (license overwrite; activation semantics) |
| **Multi-pressure context exists** | No |

---

### 18. Local event change notification handler — plugin/script writes

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/eventbus/LocalEventChangeNotificationHandler.java` |
| **Method** | EventEngine handler (blocking) |
| **Exact irreversible call** | `writeFileBlocking(classFile, ...)`, `writeFileBlocking(event.getString(SCRIPT), ...)` (L996, 1304) |
| **State mutated** | Plugin class files and script files on disk |
| **Authorization check exists** | No (writes plugin/script files; no user/permission check in same method) |
| **Ambiguity exists** | Possible (script overwrite; versioning) |
| **Multi-pressure context exists** | Yes (setBlockingEvent(true), eventBus consume, writeFileBlocking; MIX_CODE_SURFACE_EXTRACTION) |

---

### 19. ServiceOps integration upload write

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/integration/ServiceOpsIntegration.java` |
| **Method** | (method writing uploads) |
| **Exact irreversible call** | `writeFileBlocking(...UPLOADS/..., ...)` (L1242) |
| **State mutated** | Integration upload directory; external system mutation path |
| **Authorization check exists** | No |
| **Ambiguity exists** | Unclear |
| **Multi-pressure context exists** | No |

---

### 20. Atlassian Jira integration upload write

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/integration/AtlassianJiraIntegration.java` |
| **Method** | (method writing uploads) |
| **Exact irreversible call** | `writeFileBlocking(...UPLOADS/..., ...)` (L1258) |
| **State mutated** | Integration upload directory |
| **Authorization check exists** | No |
| **Ambiguity exists** | Unclear |
| **Multi-pressure context exists** | No |

---

### 21. ServiceNow integration upload write

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/integration/ServiceNowIntegration.java` |
| **Method** | (method writing uploads) |
| **Exact irreversible call** | `writeFileBlocking(...UPLOADS/..., ...)` (L1409) |
| **State mutated** | Integration upload directory |
| **Authorization check exists** | No |
| **Ambiguity exists** | Unclear |
| **Multi-pressure context exists** | No |

---

### 22. LAMA integration upload write

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/integration/LAMAIntegration.java` |
| **Method** | (method writing uploads) |
| **Exact irreversible call** | `writeFileBlocking(...UPLOADS/..., ...)` (L2020) |
| **State mutated** | Integration upload directory |
| **Authorization check exists** | No |
| **Ambiguity exists** | Unclear |
| **Multi-pressure context exists** | No |

---

### 23. UIActionEventHandler upload write

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` |
| **Method** | Handler (file upload path) |
| **Exact irreversible call** | `writeFileBlocking(...UPLOADS/...event.getString(FILE_NAME), ...)` (L3820) |
| **State mutated** | UI upload directory; file name from event |
| **Authorization check exists** | Unclear (API layer may enforce auth earlier; no getItemsByUserProfile in this handler) |
| **Ambiguity exists** | Possible (FILE_NAME from event; path traversal risk) |
| **Multi-pressure context exists** | Yes (same handler does eventBus send/request EVENT_RUNBOOK, EVENT_ADD, etc.; MIX_CODE_SURFACE_EXTRACTION) |

---

### 24. Integration engine config and pending-events persistence

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/integration/IntegrationEngine.java` |
| **Method** | init / handler |
| **Exact irreversible call** | `writeFileBlocking(INTEGRATIONS, ...)`, `writeFileBlocking(INTEGRATIONS_PENDING_EVENTS, ...)` (L135, 138, 146, 149) |
| **State mutated** | Integration config and pending events on disk |
| **Authorization check exists** | No |
| **Ambiguity exists** | Possible (pending events vs. config ordering) |
| **Multi-pressure context exists** | Yes (eventBus consumer, setBlockingEvent, writeFileBlocking; MIX_CODE_SURFACE_EXTRACTION) |

---

### 25. Motadata app manager config writes

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/manager/MotadataAppManager.java` |
| **Method** | (methods writing config) |
| **Exact irreversible call** | `writeFileBlocking(...)` config files (L719, 3035) |
| **State mutated** | Application configuration on disk |
| **Authorization check exists** | No |
| **Ambiguity exists** | Possible (config overwrite; restart semantics) |
| **Multi-pressure context exists** | No |

---

### 26. HA Observer cache writes

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/ha/Observer.java` |
| **Method** | Handler (decode/broadcast path) |
| **Exact irreversible call** | `writeFileBlocking(OBSERVER_CACHE, ...)`, `writeFileBlocking(context.getString(CACHE_NAME), ...)` (L269–270, 409, 443–444, 539–540) |
| **State mutated** | Observer cache files; HA state on disk |
| **Authorization check exists** | No (no user check in same method) |
| **Ambiguity exists** | Possible (cache name from context) |
| **Multi-pressure context exists** | Yes (executeBlocking, setBlockingEvent(true), writeFileBlocking; MIX_CODE_SURFACE_EXTRACTION) |

---

### 27. Visualization publication / datastore events (Trace History)

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/visualization/VisualizationTraceHistoryManager.java` |
| **Method** | Handler |
| **Exact irreversible call** | `eventBus().send(EVENT_PUBLICATION_DATASTORE_READ, ...)`, `eventBus().send(EVENT_ADD, ...)` (and related EVENT_* response processor sends) |
| **State mutated** | Publication/datastore read and add pipeline; downstream visibility |
| **Authorization check exists** | Yes (upstream: getItemsByUserProfile, ADMIN_ROLE at L444, 490, 502) |
| **Ambiguity exists** | Possible (qualifiedSources vs. event source filtering) |
| **Multi-pressure context exists** | Yes (eventBus send, getStore().getItem, getItemsByUserProfile, mergeIn; MIX_CODE_SURFACE_EXTRACTION) |

---

### 28. Visualization publication / datastore events (Event Manager)

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java` |
| **Method** | Handler |
| **Exact irreversible call** | Multiple `eventBus().send(EVENT_PUBLICATION_DATASTORE_READ, ...)`, `eventBus().send(EVENT_ADD, ...)`, `eventBus().send(EVENT_*_RESPONSE_PROCESSOR, ...)` |
| **State mutated** | Publication/datastore and response pipeline; UI state |
| **Authorization check exists** | Yes (getObjectIdsByUserProfile, getItemsByUserProfile, ADMIN_ROLE at L607, 609, 1312, etc.) |
| **Ambiguity exists** | Possible (queryContexts mergeIn; entity scope) |
| **Multi-pressure context exists** | Yes (eventBus send, getItemsByUserProfile, mergeIn, putAll; MIX_CODE_SURFACE_EXTRACTION) |

---

### 29. Visualization publication / datastore events (Metric Manager)

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/visualization/VisualizationMetricManager.java` |
| **Method** | Handler |
| **Exact irreversible call** | `eventBus().send(EVENT_PUBLICATION_DATASTORE_READ, ...)`, `eventBus().send(EVENT_*_RESPONSE_PROCESSOR, ...)` |
| **State mutated** | Publication/datastore and response pipeline; metric visualization state |
| **Authorization check exists** | Yes (getObjectIdsByUserProfile, getItemsByUserProfile at L694, 1344, 1418) |
| **Ambiguity exists** | Possible (queryContexts mergeIn; entity/pluginEntities) |
| **Multi-pressure context exists** | Yes (eventBus send, getItemsByUserProfile, mergeIn, putAll; MIX_CODE_SURFACE_EXTRACTION) |

---

### 30. RunbookCacheStore updateItem / complete (execution lifecycle)

| Field | Value |
|-------|--------|
| **File** | `motadata/src/main/java/com/mindarray/store/RunbookCacheStore.java` |
| **Method** | `updateItem`, `complete` |
| **Exact irreversible call** | `updateItem(id, objects.size())`; `complete(id)` (L64–91); read as `getItem(id) == NOT_AVAILABLE` guard in RunbookEngine (L389) |
| **State mutated** | Runbook execution lifecycle state (“already running”); affects whether route() is entered |
| **Authorization check exists** | N/A (guard for collision; no user scope check in store) |
| **Ambiguity exists** | Possible (check-then-act race; MIX_CODE_SURFACE_EXTRACTION) |
| **Multi-pressure context exists** | Yes (policy + UI + scheduler share same EVENT_RUNBOOK; BASE-013 covers execution boundary; this is the store mutation that gates it) |

---

**End of discovery report.**  
No phase classification or new BASE IDs proposed. All file/method/line references are from the documented Motadata artifact set (PHASE2_ARTIFACT_EXTRACTION, AUTHORITY_SURFACE_SCAN, MIX_CODE_SURFACE_EXTRACTION, PHASE1_STRUCTURAL_MAPPING, PHASE1A_BOUNDARY_DETECTION, AUTHORITY_LEAK_TRACE_FINDINGS). The actual Java codebase is not present in this repository.
