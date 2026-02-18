# MIX + CODE Surface Extraction (Structural Findings)

**Scope:** `ml/training/src/sources/Motadata` (Motadata AIOps repository)  
**Purpose:** MIX (collision detection) and CODE (implementation enforcement) candidate extraction. No phase classification applied.

---

## 1. Multi-Surface Interaction Sites

Methods/files where **two or more** of: eventBus send/request, writeFileBlocking, updateItem, mergeIn, route, scheduler, policy evaluation occur together.

| File | Method / Location | Surfaces Intersecting | Short Description |
|------|-------------------|------------------------|-------------------|
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | EventEngine handler (setEventHandler) | eventBus send/publish, writeFileBlocking, updateItem (RunbookCacheStore), mergeIn | Consumes EVENT_RUNBOOK; mergeIn(event), mergeIn(runbookContext); RunbookCacheStore.getStore().updateItem(id, objects.size()); writeFileBlocking worklog/config; publish EVENT_RUNBOOK_STATE_CHANGE, send EVENT_SCHEDULER_COMPLETE. L291–424, 447–517, 913–917, 1024–1025, 146–157. |
| `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | triggerAction | eventBus send (EVENT_RUNBOOK, EVENT_NOTIFICATION, EVENT_INTEGRATION), mergeIn(context) | policy evaluation branch; send EVENT_RUNBOOK, EVENT_INTEGRATION; request EVENT_NOTIFICATION; integrationContext = new JsonObject().mergeIn(context). L1393–1424, 3412. |
| `motadata/src/main/java/com/mindarray/policy/EventPolicyInspector.java` | triggerAction / caller | eventBus send (EVENT_RUNBOOK), policy evaluation | Sends EVENT_RUNBOOK via getContext(…); policy/event context. L1041, 1073, 1103, 1285. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationManager.java` | handler | eventBus send, getStore().getItem, mergeIn, sessions map | eventBus.send(EVENT_USER_NOTIFICATION); WidgetConfigStore.getStore().getItem(...).mergeIn(event); EventBusConstants.publish(..., UI_ACTION_VISUALIZATION_RENDER, ...); sessions.computeIfAbsent(...).put(..., new JsonObject().mergeIn(event)). L304, 460, 489, 509, 516, 672, 815, 820. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationTraceHistoryManager.java` | handler | eventBus send, getStore().getItem/getItemsByUserProfile, mergeIn | eventBus.send(EVENT_USER_NOTIFICATION, EVENT_SUCCEED, EVENT_FAIL, EVENT_VISUALIZATION_TRACE_HISTORY_RESPONSE_PROCESSOR, EVENT_PUBLICATION_DATASTORE_READ, EVENT_ADD); EventSourceConfigStore/GroupConfigStore getItemsByUserProfile; queryContexts/subQueries mergeIn(event). L198, 245, 251, 283, 317, 447, 519, 571, 444, 479, 502, 510. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java` | handler | eventBus send, getStore().getItem/getItemsByUserProfile, mergeIn, updateItem (indirect) | eventBus.send(EVENT_USER_NOTIFICATION, EVENT_SUCCEED, EVENT_FAIL, EVENT_PUBLICATION_DATASTORE_READ, EVENT_VISUALIZATION_EVENT_RESPONSE_PROCESSOR, EVENT_ADD); getObjectIdsByUserProfile/getItemsByUserProfile; queryContexts/queryUIContexts mergeIn(event); entities.putAll. L389, 460, 464, 476, 531, 542, 617, 607–609, 1312, 718, 580, 1317, 1338. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationMetricManager.java` | handler | eventBus send, getStore().getItem/getItemsByUserProfile, mergeIn, putAll | eventBus.send(EVENT_USER_NOTIFICATION, EVENT_SUCCEED, EVENT_FAIL, EVENT_PUBLICATION_DATASTORE_READ, EVENT_VISUALIZATION_METRIC_RESPONSE_PROCESSOR); getObjectIdsByUserProfile/getItemsByUserProfile; queryContexts mergeIn(event); entities/pluginEntities/entityGroups putAll. L401, 479, 483, 251, 338, 694, 794, 927, 929, 942, 1344, 1418, 1434. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationCacheEngine.java` | handler | eventBus send/publish, getStore().getItem/getItems, update(WidgetConfigStore) | vertx.eventBus().send(EVENT_VISUALIZATION, ...), publish(EVENT_VISUALIZATION_TEST); WidgetConfigStore.getStore().getItem(...); update(WidgetConfigStore.getStore().getItem(...), true). L1066, 1105, 1116, 1123, 1140, 282, 378, 471, 504. |
| `motadata/src/main/java/com/mindarray/eventbus/LocalEventChangeNotificationHandler.java` | handler | setBlockingEvent(true), eventBus (consumes), writeFileBlocking | EventEngine setBlockingEvent(true).setEventQueueSize(1); writeFileBlocking(classFile, ...), writeFileBlocking(event.getString(SCRIPT), ...). L142, 996, 1304. |
| `motadata/src/main/java/com/mindarray/store/MetricPolicyCacheStore.java` | persist path | executeBlocking, writeFileBlocking | executeBlocking(promise -> { ... writeFileBlocking(path, ...) }). L899–903. |
| `motadata/src/main/java/com/mindarray/store/ObjectStatusCacheStore.java` | persist path | executeBlocking, writeFileBlocking | executeBlocking(result -> { ... writeFileBlocking(path, ...) }). L507–511. |
| `motadata/src/main/java/com/mindarray/store/LogPatternCacheStore.java` | persist path | executeBlocking, writeFileBlocking | executeBlocking(promise -> { ... writeFileBlocking(path, ...) }). L323–327. |
| `motadata/src/main/java/com/mindarray/store/NetRouteCacheStore.java` | persist path | executeBlocking, writeFileBlocking | Two executeBlocking blocks with writeFileBlocking inside. L264–268, 284–288. |
| `motadata/src/main/java/com/mindarray/store/RUMPolicyCacheStore.java` | persist path | executeBlocking, writeFileBlocking, dirty() | executeBlocking(promise -> { ... writeFileBlocking(path, ...) }); dirty flag. L740–744, 714–716. |
| `motadata/src/main/java/com/mindarray/store/TrapCacheStore.java` | dump | writeFileBlocking, updateItem, dirty.set(true) | updateItem(trapId, value); dump() sets dirty.set(true) and writeFileBlocking(path, ...). L106–120, 129–137. |
| `motadata/src/main/java/com/mindarray/integration/IntegrationEngine.java` | init/ handler | eventBus (consumes), writeFileBlocking | setBlockingEvent(true); writeFileBlocking(INTEGRATIONS, ...), writeFileBlocking(INTEGRATIONS_PENDING_EVENTS, ...). L134–149. |
| `motadata/src/main/java/com/mindarray/ha/Observer.java` | handler | executeBlocking, setBlockingEvent(true), writeFileBlocking | setBlockingEvent(true).setEventQueueSize(1); executeBlocking(...); writeFileBlocking(OBSERVER_CACHE, ...), writeFileBlocking(context.getString(CACHE_NAME), ...). L296, 255, 409, 269–270, 443–444, 539–540. |
| `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` | multiple handlers | eventBus send/request (EVENT_ADD, EVENT_RUNBOOK, EVENT_ROUTER, EVENT_PUBLICATION, etc.), writeFileBlocking | eventBus.send(EVENT_ADD, EVENT_RUNBOOK, EVENT_PROGRESS_UPDATE, EVENT_ROUTER, ...); writeFileBlocking(UPLOADS/..., ...). L399, 521, 609, 705, 771, 843, 952, 1331, 1819, 1930, 1968, 2157, 2162, 3732, 3820, etc. |

---

## 2. Concurrency Collision Sites

| File | Method / Location | Shared State | Potential Interaction Risk |
|------|-------------------|--------------|-----------------------------|
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | EventEngine handler | RunbookCacheStore.getStore(), worklogs (Map), eventEngine | Single consumer but policy + UI + scheduler can enqueue same runbook id; getItem(id) == NOT_AVAILABLE guards “already running”; updateItem(id, objects.size()) and complete(id) mutate shared store. L389, 393, 910–917, 75–77 (RunbookCacheStore). |
| `motadata/src/main/java/com/mindarray/store/RunbookCacheStore.java` | getItem, updateItem, complete | items (ConcurrentHashMap<Long, Integer>) | Read by RunbookEngine to skip if already running; updated by RunbookEngine; complete(id) from same handler. No lock around “check then update” — theoretical race if two events for same id arrive. L64–91. |
| `motadata/src/main/java/com/mindarray/store/TrapCacheStore.java` | updateItem, dump | items (ConcurrentHashMap), dirty (AtomicBoolean), updated (boolean) | updated set in updateItem; dump() reads updated and sets dirty + writeFileBlocking. Non-atomic updated vs dirty. L56, 106–120, 129–137. |
| `motadata/src/main/java/com/mindarray/store/RUMPolicyCacheStore.java` | persist path | dirty (AtomicBoolean), items | executeBlocking + writeFileBlocking; dirty()/setDirty used for persistence. L89, 714–716, 740–744. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationManager.java` | handler | sessions (Map<Long, Map<String, JsonObject>>), queryStatuses, cachedItems | sessions updated and read across async reply handlers; forEach over sessions.get(queryId) while publishing. L119, 324, 356–369, 509, 516, 815, 820, 842. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationCacheEngine.java` | handler | sessionsByWidget, sessionsByContext, WidgetConfigStore.getStore() | getItem(id) and update(...) on widget store; sessionsByWidget/sessionsByContext updated from events. L282, 347, 378, 460, 471, 504, 1066, 1140. |
| `motadata/src/main/java/com/mindarray/nms/ObjectManager.java` | EventEngine handler | setBlockingEvent(true).setEventQueueSize(1) | Single-threaded queue; shared event handler. L696. |
| `motadata/src/main/java/com/mindarray/notification/NotificationEngine.java` | EventEngine handler | setBlockingEvent(true) | Blocking consumer; shared handler. L140. |
| `motadata/src/main/java/com/mindarray/eventbus/LocalEventChangeNotificationHandler.java` | EventEngine handler | setBlockingEvent(true).setEventQueueSize(1) | Single-threaded; config/script writeFileBlocking in handler. L142. |
| `motadata/src/main/java/com/mindarray/plugin/PluginEngine.java` | workerExecutor.executeBlocking | workerExecutor, plugin execution state | executeBlocking(future -> ...) per request; shared worker pool. L392. |
| `motadata/src/main/java/com/mindarray/plugin/PluginEngineResponseProcessor.java` | setBlockingEvent(true) + executeBlocking | EventEngine + vertx.executeBlocking | setBlockingEvent(true); inside handler vertx.executeBlocking(future -> ...). L96, 104. |
| `motadata/src/main/java/com/mindarray/nms/MetricPoller.java` | metricWorkerExecutors / availabilityWorkerExecutors / networkServiceWorkerExecutors | executeBlocking per entry key | executeBlocking on worker pools keyed by plugin/type; shared caches (ObjectStatusCacheStore, etc.). L440, 541, 662. |
| `motadata/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java` | multiple methods | vertx.executeBlocking, DB/cache access | executeBlocking used for policy fetch; shared cache/DB. L125, 167, 211, 229, 247, 266, 284, 308, 330, 352, 1974, 1993. |
| `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` | handlers | executeBlocking(future -> ...), eventBus request(EVENT_RUNBOOK) | vertx.executeBlocking in UI flows; request(EVENT_RUNBOOK, ...) shares RunbookEngine with policy/scheduler. L427, 477, 1141, 1968, 3212, 3708, 3812, 3732. |

---

## 3. Manual vs Automated Collision Candidates

| File | Execution Path | Shared Resource |
|------|----------------|-----------------|
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | EVENT_RUNBOOK consumer | RunbookEngine handler; RunbookCacheStore (getItem/updateItem/complete); worklogs map; ObjectConfigStore.getStore().getItems(...); writeFileBlocking worklog/config. |
| `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` | UI: vertx.eventBus().request(EVENT_RUNBOOK, context) (L1968); vertx.eventBus().send(EVENT_RUNBOOK, event.copy()...) (L2157, 2162); request(EVENT_RUNBOOK, event.put(ID, id)) (L3732) | Same EVENT_RUNBOOK address; RunbookEngine consumes; RunbookCacheStore. |
| `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | triggerAction: eventBus().send(EVENT_RUNBOOK, prepareContext(...)) (L1403) | Same EVENT_RUNBOOK; RunbookEngine. |
| `motadata/src/main/java/com/mindarray/policy/EventPolicyInspector.java` | triggerAction: eventBus().send(EVENT_RUNBOOK, getContext(...)) (L1285) | Same EVENT_RUNBOOK; RunbookEngine. |
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | Branch by EVENT_SCHEDULER vs UI_EVENT_UUID / UI_ACTION_RUNBOOK_PLUGIN_TEST (L302, 381, 389, 403, 910–917) | Scheduler and manual both use same handler; EVENT_SCHEDULER_COMPLETE sent only when event.containsKey(EVENT_SCHEDULER). |

---

## 4. Fail-Closed Enforcement Sites

| File | Method / Location | Guard Condition | Protected Action |
|------|-------------------|-----------------|------------------|
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | qualify(JsonObject context, JsonObject runbook, Promise<JsonObject> promise) | CONFIG category: context.getString(CONFIG_MANAGEMENT_STATUS, EMPTY_VALUE).equalsIgnoreCase(YES) → allow; else complete with STATUS_FAIL and return false | Blocks runbook execution for CONFIG category when config.management.status != YES. L1065–1091. |
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | EventEngine handler | if (!runbook.containsKey(EVENT_SCHEDULER) \|\| RunbookCacheStore.getStore().getItem(id) == NOT_AVAILABLE) → enter block; else skip | Prevents starting runbook if already running (getItem(id) != NOT_AVAILABLE). L389. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationQueryHelper.java` | reply handler | message.reply(new JsonObject().put(STATUS, STATUS_FAIL).put(ERRORS, ...)); event.put(STATUS, STATUS_FAIL)... | Fail reply on exception/timeout. L138, 163, 180, 210. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationTraceHistoryResponseProcessor.java` | (method) | return false | Early exit on invalid state. L126. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationRUMHistoryResponseProcessor.java` | (method) | return false | Early exit. L98, 968, 988. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationCacheEngine.java` | (method) | return false; message.fail(NOT_AVAILABLE, ...) | Validation/availability failure. L1191, 1222, 1615, 1636, 1649, 302. |
| `motadata/src/main/java/com/mindarray/util/UserNotificationUtil.java` | (method) | message.reply(new JsonObject().put(STATUS, STATUS_FAIL).put(MESSAGE, USER_NOT_FOUND)) | Fail reply when user not found. L128. |
| `motadata/src/main/java/com/mindarray/util/WorkerUtil.java` | send / extractErrorCode | result.put(STATUS, STATUS_FAIL); send(..., STATUS_FAIL, ...) | Propagate failure status to event bus. L274, 380, 449, 463, 490, 899, 931, 946. |
| `motadata/src/main/java/com/mindarray/util/ProcessUtil.java` | (method) | .put(GlobalConstants.STATUS, GlobalConstants.STATUS_FAIL) | Event payload on failure. L295. |
| `motadata/src/main/java/com/mindarray/util/HealthUtil.java` | (method) | message.body().put(..., STATUS_FAIL); EventBusConstants.publish(..., STATUS_FAIL) | Health stats failure publish. L274. |
| `motadata/src/main/java/com/mindarray/util/EmailUtil.java` | (method) | message.fail(GlobalConstants.NOT_AVAILABLE, ...) | Fail reply on email/template errors. L177, 350, 361, 411, 438. |
| `motadata/src/main/java/com/mindarray/util/ProxyServiceUtil.java` | (method) | message.fail(NOT_AVAILABLE, ...) | Proxy error fail. L136, 144. |
| `motadata/src/main/java/com/mindarray/job/JobScheduler.java` | (method) | throw new IllegalStateException("Access not available") | Blocks access when not available. L130. |
| `motadata/src/main/java/com/mindarray/eventbus/EventStore.java` | (method) | throw new Exception("writer is null..."); throw new Exception("store name can not be blank..."); throw on segment open failure | Fail-closed on invalid store state. L251, 374, 414. |
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | qualify() | promise.complete(STATUS_FAIL); complete(context.put(STATUS, STATUS_FAIL)...); return false | CONFIG runbook not run when config.management.status != YES. L1076–1088. |

---

## 5. Hard Boundary Enforcement Sites

| File | Method / Location | Guard | Boundary Protected |
|------|-------------------|-------|--------------------|
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | EventEngine handler | RunbookCacheStore.getStore().getItem(id) == NOT_AVAILABLE required to proceed; else block skipped | Prevents concurrent execution of same runbook id; “already running” boundary. L389. |
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | qualify() | CONFIG_MANAGEMENT_STATUS == YES required for CONFIG runbook; else complete with FAIL and return false | No partial execution of CONFIG runbook when config management off. L1067–1090. |
| `motadata/src/main/java/com/mindarray/store/RunbookCacheStore.java` | getItem(long id) | Returns NOT_AVAILABLE when id not in cache | Caller treats NOT_AVAILABLE as “not running”; used as guard before updateItem. L75–77. |
| `motadata/src/main/java/com/mindarray/store/TrapCacheStore.java` | dump() | if (updated) { updated = false; dirty.set(true); writeFileBlocking(...) } | Persistence only when updated; dirty flag marks need to persist. L129–137. |
| `motadata/src/main/java/com/mindarray/store/TrapCacheStore.java` | dirty(), setDirty() | AtomicBoolean dirty | External visibility of dirty state for persistence flow. L56, 113–120. |
| `motadata/src/main/java/com/mindarray/store/RUMPolicyCacheStore.java` | dirty(), setDirty() | AtomicBoolean dirty | Same pattern; persistence gated by dirty. L89, 714–716. |
| `motadata/src/main/java/com/mindarray/nms/ObjectManager.java` | EventEngine | setEventQueueSize(1) | Single in-flight event per consumer; serialized execution. L696. |
| `motadata/src/main/java/com/mindarray/eventbus/LocalEventChangeNotificationHandler.java` | EventEngine | setEventQueueSize(1) | Single in-flight; serialized config/script writes. L142. |
| `motadata/src/main/java/com/mindarray/ha/Observer.java` | EventEngine | setEventQueueSize(1) | Single in-flight decode/broadcast. L296. |

---

## 6. Safe Default Patterns

| File | Method / Location | Default Behavior |
|------|-------------------|------------------|
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | qualify() | context.getString(Configuration.CONFIG_MANAGEMENT_STATUS, EMPTY_VALUE) — default EMPTY_VALUE; CONFIG runbook only runs when YES. L1069. |
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | handler | runbook.getString(USER_NAME, DEFAULT_USER) for availabilityProbe. L434. |
| `motadata/src/main/java/com/mindarray/store/RunbookCacheStore.java` | getItem(long id) | getOrDefault(id, GlobalConstants.NOT_AVAILABLE) — default NOT_AVAILABLE when not in cache. L77. |
| `motadata/src/main/java/com/mindarray/store/ConfigurationConfigStore.java` | (method) | item.containsKey(Configuration.CONFIG_MANAGEMENT_STATUS) before getString. L98, 142, 160. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java` | (handler) | subQueryContext.getString("container.type", "dashboard"); event.containsKey("cache") && event.getBoolean("cache", Boolean.FALSE); subQueryContext.getString("drill.down.type", "no"). L1338. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationMetricManager.java` | (handler) | subQueryContext.getString(CONTAINER_TYPE, "dashboard"); subQueryContext.getString("drill.down.type", "no"). L1434. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationRUMHistoryResponseProcessor.java` | (method) | dataSource.getString("sub.category", ""). L180, 191, 202, 213, 224. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationTraceHistoryResponseProcessor.java` | (method) | event.getString("http.request.method", "-"); event.getString("url.path", "-"). L648, 650. |
| `motadata/src/main/java/com/mindarray/store/MetricPolicyCacheStore.java` | severity handling | if (severity.equals(Severity.DOWN)) severities.add(Severity.CRITICAL) — DOWN mapped to CRITICAL for object severity. L259–261, 303, 319. |
| `motadata/src/main/java/com/mindarray/store/RUMPolicyCacheStore.java` | severity handling | Same: Severity.DOWN → add Severity.CRITICAL. L287–289, 311, 327. |
| `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | triggerAction | severity remap for runbook: POLICY_TYPE AVAILABILITY + INSTANCE non-empty → CRITICAL becomes DOWN. L1392. |
| `motadata/src/main/java/com/mindarray/util/Logger.java` | (method) | LoggerCacheStore.getStore().qualify(this.module) — gating by module. L432, 545. |
| `motadata/src/main/java/com/mindarray/store/LoggerCacheStore.java` | qualify(String module) | Returns boolean for whether to log; config gating. L71. |
| `motadata/src/main/java/com/mindarray/util/MotadataConfigUtil.java` | (multiple) | return false on validation failure (e.g. invalid config). L1286, 1296, 2497, 2527, 2615, 3711, 3724, 4011, 4158, 4264, 4367, 4393. |
| `motadata/src/main/java/com/mindarray/util/DateTimeUtil.java` | (method) | return false for invalid range. L955. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationCacheEngine.java` | (method) | if (context == null) return false. L1615. |

---

**End of extraction.**  
No phase (MIX/CODE) or REF/CONF/DES classification applied. File paths relative to `ml/training/src/sources/Motadata/`.
