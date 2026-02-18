# Authority Surface Scan — Candidate REF Artifacts (Code-Backed)

**Scope:** `ml/training/src/sources/Motadata` (Motadata AIOps repository)  
**Purpose:** Structural extraction of sites where authority, ownership, or legitimacy boundaries may be relevant. No phase classification (REF/CONF/DES) applied.

---

## 1. Authority Check Sites

| File | Method / Location | Line | Condition Summary |
|------|-------------------|------|-------------------|
| `motadata/src/main/java/com/mindarray/store/GroupConfigStore.java` | `getItemsByUserProfile(long userId)` | 214 | Returns group IDs by user profile scope (GROUP vs default); DEFAULT_ID gets all groups; else profile context ENTITIES or empty. |
| `motadata/src/main/java/com/mindarray/store/ObjectConfigStore.java` | `getItemsByUserProfile(long userId)` | 505 | Delegates to GroupConfigStore.getItemsByUserProfile(userId); returns object items filtered by user's groups. |
| `motadata/src/main/java/com/mindarray/store/ObjectConfigStore.java` | `getObjectIdsByUserProfile(long userId)` | 594 | Same group-based filtering; returns object IDs accessible to user. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationTraceHistoryManager.java` | (handler) | 444 | `getItemsByUserProfile(user.getLong(ID))` used to compute qualifiedSources for event source filtering. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationTraceHistoryManager.java` | (handler) | 490, 502 | `event.put(ADMIN_ROLE, adminRole)`; subQueryContext includes ADMIN_ROLE. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java` | (handler) | 607, 609 | `getObjectIdsByUserProfile(user.getLong(ID))`, `getItemsByUserProfile(user.getLong(ID))` for qualifiedObjects / qualifiedSources. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java` | (handler) | 742, 921, 942, 973, 987, 1266, 1279, 1312, 1317 | `event.put(VisualizationConstants.ADMIN_ROLE, ...)` in multiple branches; 1312 uses `getItemsByUserProfile(user.getLong(ID))`. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationMetricManager.java` | (handler) | 694, 1344, 1418 | `getObjectIdsByUserProfile(user.getLong(ID))`; `getItemsByUserProfile(user.getLong(ID))`; subQueryContext ADMIN_ROLE. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationRUMHistoryManager.java` | (handler) | 438, 484, 496 | `getItemsByUserProfile(user.getLong(ID))`; event/subQueryContext ADMIN_ROLE. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationAvailabilityManager.java` | (handler) | 593, 1282 | `getObjectIdsByUserProfile(user.getLong(ID))`; `getItemsByUserProfile(user.getLong(ID))`. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationEventHistoryManager.java` | (handler) | 465, 532 | `getItemsByUserProfile(user.getLong(ID))`; `getObjectIdsByUserProfile(user.getLong(ID))`. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java` | (static helpers) | 2607, 2967, 3560 | `getItemsByUserProfile(userId)` / `user.getLong(ID)` for qualified groups. |
| `motadata/src/main/java/com/mindarray/policy/SeverityChangeEventProcessor.java` | (handler) | 219, 429 | `getObjectIdsByUserProfile(userId)` for notification filtering. |
| `motadata/src/main/java/com/mindarray/report/ReportManager.java` | (handler) | 290, 294, 458, 462 | `getItemsByUserProfile(user.getLong(ID), ...)` for widget/object filtering. |
| `motadata/src/main/java/com/mindarray/job/CustomJob.java` | (handler) | 768 | `getItemsByUserProfile(user.getLong(ID))`. |
| `motadata/src/main/java/com/mindarray/db/ConfigDBChangeEventProcessor.java` | (handler) | 186, 283 | `getItemsByUserProfile(user.getLong(ID), ...)` for config change visibility. |
| `motadata/src/main/java/com/mindarray/api/Template.java` | (API) | 802, 843 | `routingContext.user().principal().getLong(ID)`; `getItemsByUserProfile(userId, objectIds)`. |
| `motadata/src/main/java/com/mindarray/api/SNMPDeviceCatalog.java` | (API) | 283, 348 | `getItemsByUserProfile(routingContext.user().principal().getLong(ID), entityIds)`. |
| `motadata/src/main/java/com/mindarray/api/TopologyPlugin.java` | (API) | 272, 285, 340, 344 | `getItemsByUserProfile(routingContext.user().principal().getLong(ID), ...)` and `getItemsByUserProfile(response.getLong(USER_ID), ...)`. |
| `motadata/src/main/java/com/mindarray/api/RunbookPlugin.java` | (API) | 393, 404, 497, 501 | Same pattern: principal/USER_ID + getItemsByUserProfile. |
| `motadata/src/main/java/com/mindarray/api/Query.java` | (API) | 126, 148, 169 | `getItemsByUserProfile(routingContext.user().principal().getLong(ID), ...)`. |
| `motadata/src/main/java/com/mindarray/api/MetricPlugin.java` | (API) | 777, 788, 843, 847 | Same: principal/USER_ID + getItemsByUserProfile. |
| `motadata/src/main/java/com/mindarray/api/Group.java` | (API) | 97 | `getItemsByUserProfile(user.getLong(ID))` for tree. |
| `motadata/src/main/java/com/mindarray/api/MetricPolicy.java` | (API) | 121, 126, 135, 139, 217, 228, 236, 240 | `routingContext.user().principal().getLong(ID)` / `response.getLong(USER_ID)` + getItemsByUserProfile for policy entity scoping. |

**Note:** No occurrences of `hasPermission`, `isAuthorized`, `isOwner`, `checkAccess`, `validateUser`, `SecurityContext`, `ACL`, `CODEOWNERS`, or `requiresApproval` in the scanned code. Authority is expressed via user-profile–scoped data (getItemsByUserProfile / getObjectIdsByUserProfile) and ADMIN_ROLE in visualization context.

---

## 2. Potential Execution Without Explicit Authority

| File | Method / Location | Action | Authority Check Present? | Evidence |
|------|-------------------|--------|---------------------------|----------|
| `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | `triggerAction` (runbook branch) | `eventBus().send(EVENT_RUNBOOK, prepareContext(...))` | NO | No user/principal or getItemsByUserProfile in method; policy/context/entityId only. L1393–1409. |
| `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | same | `eventBus().send(EVENT_INTEGRATION, integrationContext)` | NO | Same method; no user/authority check before send. L1424. |
| `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | (notification paths) | `eventBus().request(EVENT_NOTIFICATION, ...)` | NO | Trigger path uses policy/context; no explicit authority check in same method. L1259, 1288, 1478, 1504, 3225, 3254, 3425, 3451. |
| `motadata/src/main/java/com/mindarray/policy/EventPolicyInspector.java` | `triggerAction` / caller | `eventBus().send(EVENT_RUNBOOK, getContext(...))` | NO | No getItemsByUserProfile or user check in dispatch path. L1285. |
| `motadata/src/main/java/com/mindarray/policy/EventPolicyInspector.java` | (notification) | `eventBus().request(EVENT_NOTIFICATION, ...)` | NO | L1152, 1191. |
| `motadata/src/main/java/com/mindarray/policy/NetRoutePolicyInspector.java` | (notification) | `eventBus().request(EVENT_NOTIFICATION, ...)` | NO | L758, 796, 905, 935. |
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | EventEngine handler | Executes runbook (SSH/PowerShell/HTTP etc.); `writeFileBlocking` worklog/config | NO | Handler uses RunbookPluginConfigStore.getItem(event.getLong(ID)), ObjectConfigStore.getItems/getItemsByGroups — no getItemsByUserProfile; no user/principal in execution path. L291–424, 1024–1025, 146–157. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationTraceHistoryManager.java` | (handler) | `eventBus().send(EVENT_PUBLICATION_DATASTORE_READ, ...)`, `eventBus().send(EVENT_ADD, ...)` | YES (upstream) | Same flow uses getItemsByUserProfile and ADMIN_ROLE earlier in request path (e.g. 444, 490, 502). |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java` | (handler) | Multiple `eventBus().send` (EVENT_PUBLICATION_DATASTORE_READ, EVENT_ADD, EVENT_*_RESPONSE_PROCESSOR) | YES (upstream) | getObjectIdsByUserProfile/getItemsByUserProfile and ADMIN_ROLE used in same handler flow (607, 609, 1312, etc.). |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationMetricManager.java` | (handler) | `eventBus().send(EVENT_PUBLICATION_DATASTORE_READ, ...)`, etc. | YES (upstream) | getObjectIdsByUserProfile/getItemsByUserProfile at 694, 1344; ADMIN_ROLE at 1418. |
| `motadata/src/main/java/com/mindarray/util/ShutdownUtil.java` | (method) | `writeFileBlocking(PATH, ...)` | NO | No user/permission check in same method. L259. |
| `motadata/src/main/java/com/mindarray/util/DiagnosticUtil.java` | (method) | `writeFileBlocking(...engine-stats.json, ...)`, `writeFileBlocking(...faulty-objects.json, ...)` | NO | No authority check in same method. L65, 162. |
| `motadata/src/main/java/com/mindarray/util/LogUtil.java` | (method) | `writeFileBlocking(...agent.json, ...)`, `writeFileBlocking(...motadata.json, ...)` | NO | L247, 262. |
| `motadata/src/main/java/com/mindarray/util/LicenseUtil.java` | (method) | `writeFileBlocking(LICENSE_PATH, ...)`, `writeFileBlocking(LICENSE_FILE, ...)` | NO | L380, 624, 863. |
| `motadata/src/main/java/com/mindarray/eventbus/LocalEventChangeNotificationHandler.java` | (handler) | `writeFileBlocking(classFile, ...)`, `writeFileBlocking(event.getString(SCRIPT), ...)` | NO | Writes plugin/script files; no user/permission check in same method. L996, 1304. |
| `motadata/src/main/java/com/mindarray/integration/ServiceOpsIntegration.java` | (method) | `writeFileBlocking(...UPLOADS/..., ...)` | NO | L1242. |
| `motadata/src/main/java/com/mindarray/integration/AtlassianJiraIntegration.java` | (method) | `writeFileBlocking(...UPLOADS/..., ...)` | NO | L1258. |
| `motadata/src/main/java/com/mindarray/integration/ServiceNowIntegration.java` | (method) | `writeFileBlocking(...UPLOADS/..., ...)` | NO | L1409. |
| `motadata/src/main/java/com/mindarray/integration/LAMAIntegration.java` | (method) | `writeFileBlocking(...UPLOADS/..., ...)` | NO | L2020. |
| `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` | (handler) | `writeFileBlocking(...UPLOADS/...event.getString(FILE_NAME), ...)` | Unclear | UI action path; no explicit getItemsByUserProfile in same method; API layer may enforce auth earlier. L3820. |

---

## 3. Context Reuse Sites

| File | Method / Location | Risk Description |
|------|-------------------|-------------------|
| `motadata/src/main/java/com/mindarray/visualization/VisualizationManager.java` | (handler) | `WidgetConfigStore.getStore().getItem(event.getLong(ID)).mergeIn(event)`; session map keyed by sessionId+uiEventUuid; context merged from widget config and event without re-validating user/tenant. L460, 489, 509, 516, 614–615, 622, 625, 628, 631, 635, 638, 815, 820, 912, 914, 916. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationRUMHistoryManager.java` | (handler) | `eventColumns.mergeIn(reply.result().body().getJsonObject(DatastoreConstants.EVENT_COLUMNS))`; `queryContexts.put(..., new JsonObject().mergeIn(event)...)`; subQueryContext mergeIn(event) and mergeIn(visualizationDataSource). L114, 473, 496, 506. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationMetricManager.java` | (handler) | `metricColumns.mergeIn(reply.result().body().getJsonObject(...))`; `new JsonObject().mergeIn(context)`; `queryContexts.put(..., new JsonObject().mergeIn(event)...)`; `entities.putAll(qualifiedEntities.get(ENTITIES))`; `pluginEntities.putAll(...)`; `entityGroups.putAll(...)`. L275, 431, 794, 927, 929, 942, 1130, 1209, 1293, 1418, 1434. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java` | (handler) | `eventColumns.mergeIn(...)`; `queryUIContexts.computeIfAbsent(..., value -> new JsonObject().mergeIn(event))`; `queryContexts.put(..., new JsonObject().mergeIn(event)...)`; `entities.putAll(...)`; subQueryContext/queryContext mergeIn. L225, 580, 718, 869, 888, 963, 1093, 1317, 1338, 1647. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationTraceHistoryManager.java` | (handler) | Same pattern: eventColumns.mergeIn; queryContexts/subQueries mergeIn(event) and mergeIn(visualizationDataSource). L118, 479, 502, 510. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationAvailabilityManager.java` | (handler) | metricColumns.mergeIn; queryContexts mergeIn(event); entities.putAll/pluginEntities.putAll. L167, 323, 697, 756, 767, 779, 818, 1053, 1055. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationRUMHistoryResponseProcessor.java` | (method) | `queryTicks.get(queryId).putAll(queryData.ticks)`. L868. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationMetricResponseProcessor.java` | (method) | `visualizationContext.getJsonObject(VISUALIZATION_PROPERTIES).mergeIn(context.getJsonObject(...))`; `new JsonObject().mergeIn(dataPoint)`. L190, 196, 403, 459. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationQueryHelper.java` | (method) | Timeline/context merge: `context.put(..., new JsonObject().put(...).mergeIn(event.getJsonObject("timeline")))`. L345. |
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | EventEngine handler | `runbook.mergeIn(event)`; `runbook.mergeIn(runbook.getJsonObject(RUNBOOK_PLUGIN_CONTEXT))`; `object.mergeIn(object.getJsonObject(OBJECT_CONTEXT))`; `object.mergeIn(runbookContext)`; proxy config mergeIn from store. Event-derived context merged into runbook/object without re-checking tenant/user at execution. L314, 319–324, 418–424, 335–336. |
| `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | `triggerAction` | `integrationContext = new JsonObject().mergeIn(context).put(POLICY_ID, ...)`. Context from policy evaluation merged and sent to EVENT_INTEGRATION. L3412. |

**Global/static store usage without tenant filter (candidate for cross-tenant reuse):**

| File | Location | Risk Description |
|------|----------|-------------------|
| `motadata/src/main/java/com/mindarray/util/DNSUtil.java` | L127 | `ObjectConfigStore.getStore().getItems()` passed to resolver when DNS object resolution enabled; no user/tenant filter. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationCacheEngine.java` | L347 | `WidgetConfigStore.getStore().getItems()` used; no user filter in call. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java` | L2621, 4830, 4860 | `LogParserConfigStore.getStore().getItems()`, `SLOCycleConfigStore.getStore().getItems()`, `RemoteEventProcessorConfigStore.getStore().getItems()` used in helpers; context may carry userId but store access is global. |
| `motadata/src/main/java/com/mindarray/store/ObjectConfigStore.java` | L326–328 | `populateItemsByProfile(UserProfileConfigStore.getStore().getItems())`, `populateItemsByUser(UserConfigStore.getStore().getItems())` — bulk load for caching, not request-scoped. |
| `motadata/src/main/java/com/mindarray/util/OAuthUtil.java` | L255 | `ActiveUserCacheStore.getStore().getItems().entrySet()` — global store iteration. |

---

## 4. Implicit Authority Boundaries

| File | Action | Guard Present? | Evidence |
|------|--------|----------------|----------|
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | Execute runbook (SSH/PowerShell/HTTP/Ansible etc.) on targets from event/policy context | NO | No getItemsByUserProfile or user principal in consumer; permission/ownership inferred from policy configuration and entity context, not verified at execution site. |
| `motadata/src/main/java/com/mindarray/runbook/RunbookEngine.java` | `writeFileBlocking` (worklog dir, config, uploads) | NO | No permission check in same method. L147, 157, 1025. |
| `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | Send EVENT_RUNBOOK (policy-triggered runbook execution) | NO | triggerAction does not check user/principal; authority assumed from policy/trigger path. |
| `motadata/src/main/java/com/mindarray/policy/EventPolicyInspector.java` | Send EVENT_RUNBOOK (event-policy–triggered runbook) | NO | Same: no explicit permission check at dispatch. |
| `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | `eventBus().request(EVENT_NOTIFICATION, ...)` (email/SMS etc.) | NO | Notification sent based on policy/context; no local verification of “who is allowed to send” in this method. |
| `motadata/src/main/java/com/mindarray/integration/IntegrationEngine.java` | `writeFileBlocking` (INTEGRATIONS, INTEGRATIONS_PENDING_EVENTS) | NO | L135, 138, 146, 149. |
| `motadata/src/main/java/com/mindarray/integration/ServiceOpsIntegration.java` | Write file under UPLOADS (external system mutation path) | NO | L1242. |
| `motadata/src/main/java/com/mindarray/integration/AtlassianJiraIntegration.java` | Write file under UPLOADS | NO | L1258. |
| `motadata/src/main/java/com/mindarray/integration/ServiceNowIntegration.java` | Write file under UPLOADS | NO | L1409. |
| `motadata/src/main/java/com/mindarray/integration/LAMAIntegration.java` | Write file under UPLOADS | NO | L2020. |
| `motadata/src/main/java/com/mindarray/eventbus/LocalEventChangeNotificationHandler.java` | Write plugin script/class file to disk | NO | L996, 1304. |
| `motadata/src/main/java/com/mindarray/util/LicenseUtil.java` | writeFileBlocking LICENSE_PATH / LICENSE_FILE | NO | L380, 624, 863. |
| `motadata/src/main/java/com/mindarray/manager/MotadataAppManager.java` | writeFileBlocking config files | NO | L719, 3035. |
| `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` | writeFileBlocking to UPLOADS with event.getString(FILE_NAME) | Unclear | Depends on prior API/auth; no guard in this handler. L3820. |

---

**End of scan.**  
No REF/CONF/DES classification applied. File references are to paths under `ml/training/src/sources/Motadata/`.
