# Authority Leak Trace — Code-Backed Findings

**Scope:** `ml/training/src/sources/Motadata`  
**Bug:** User with access to 5 monitors can see (fully or partially) details of other 5 monitors when a policy is attached to 10 monitors.

---

## STEP 1 — Policy → Monitor Resolution

### Policy-to-Monitor Resolution Sites

| File | Method | How monitors are retrieved | getItemsByUserProfile used? |
|------|--------|----------------------------|-----------------------------|
| `motadata/src/main/java/com/mindarray/store/MetricPolicyCacheStore.java` | `getItems(JsonArray entities)` | L381–421: Iterates `entities` (object IDs), uses `policyKeysByObject.get(entities.getLong(index))` to get policy keys per entity; returns `getItem(hashCode)` per key. No filtering by user. | **NO** |
| `motadata/src/main/java/com/mindarray/store/MetricPolicyCacheStore.java` | `getItemsByCategory(JsonArray entities, String category)` | L423–467: Same pattern: iterates `entities`, uses `policyKeysByObject.get(entityId)`, returns policy items by key. No user check. | **NO** |
| `motadata/src/main/java/com/mindarray/store/MetricPolicyCacheStore.java` | `getItemsBySeverity(String severity)` | L813–831: Iterates `objects.entrySet()` (all objects in cache with that severity), builds JsonArray with ID, OBJECT_NAME, OBJECT_IP, SEVERITY, OBJECT_ID. No user/profile filter. | **NO** |
| `motadata/src/main/java/com/mindarray/store/MetricPolicyCacheStore.java` | `getSeverity(long id)` / `getInstanceSeverity(String entity)` / `getSeveritiesByObject(long id)` | Used for severity/stat columns; accept single id/entity. No user check inside store. | **NO** |
| `motadata/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java` | `getPolicyCounts(JsonObject context)` | L382–447: Uses `context.getJsonArray(ENTITIES)`; for GROUP_BY monitor uses `getSeverity(CommonUtil.getLong(entity))` per entity; else uses `MetricPolicyCacheStore.getStore().getItemsByCategory(context.getJsonArray(ENTITIES), ...)`. ENTITIES come from caller; no getItemsByUserProfile in this class. | **NO** |
| `motadata/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java` | `getMetricPolicies(JsonObject context, String type)` | L483–489: `var items = MetricPolicyCacheStore.getStore().getItems(context.getJsonArray(ENTITIES))`. ENTITIES from context; no filtering here. | **NO** |
| `motadata/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java` | `buildHeatmapByObjects(JsonObject context, JsonObject result)` | L1117–1118: `var items = MetricPolicyCacheStore.getStore().getItems(context.getJsonArray(ENTITIES))`. L1146–1166: If no POLICIES in context, iterates `context.getJsonArray(ENTITIES)` and calls `getSeverity(entities.getLong(index))`. No user filter. | **NO** |
| `motadata/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java` | `buildHeatmapByApplications(JsonObject context, JsonObject result)` | L1204: `var items = MetricPolicyCacheStore.getStore().getItems(context.getJsonArray(ENTITIES))`. No user filter. | **NO** |

**Conclusion:** Policy-to-monitor resolution is entirely driven by the `ENTITIES` (or severity) passed in context. **MetricPolicyCacheStore and PolicyCacheServiceImpl do not call getItemsByUserProfile or getObjectIdsByUserProfile.** Filtering depends entirely on the caller.

---

## STEP 2 — User Visibility Filtering

### User Visibility Filtering Sites

| File | Method | Filtering condition | Scope |
|------|--------|--------------------|-------|
| `motadata/src/main/java/com/mindarray/store/GroupConfigStore.java` | `getItemsByUserProfile(long userId)` | L214–239: DEFAULT_ID → all groups; else profile scope (GROUP → context ENTITIES; default → empty) or user's USER_GROUPS. | Internal (used by ObjectConfigStore and visualization) |
| `motadata/src/main/java/com/mindarray/store/ObjectConfigStore.java` | `getItemsByUserProfile(long userId)` | L505–509: Delegates to GroupConfigStore.getItemsByUserProfile; returns getItemsByGroups(groupIds) or getItemsByTag(userId). | Internal |
| `motadata/src/main/java/com/mindarray/store/ObjectConfigStore.java` | `getObjectIdsByUserProfile(long userId)` | L594–605: Same group/tag-based logic; returns object IDs accessible to user. | Internal |
| `motadata/src/main/java/com/mindarray/store/ObjectConfigStore.java` | `getItemsByUserProfile(long userId, JsonArray ids)` | L573–585: Filters `ids` to those in user's groups (getIdsByGroups) or by tag. | Internal / API |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java` | (handler) | L607: `qualifiedObjects = ObjectConfigStore.getStore().getObjectIdsByUserProfile(user.getLong(ID))...`; L609: `qualifiedSources = ... getItemsByUserProfile(user.getLong(ID))`. Used to build qualifiedObjects/qualifiedSources before building ENTITIES for policy cache. | UI/Internal (event visualization) |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationMetricManager.java` | (handler) | L694: `qualifiedObjects = ObjectConfigStore.getStore().getObjectIdsByUserProfile(user.getLong(ID))...`. Used before qualifyEntities and before passing ENTITIES to cache. | UI/Internal (metric visualization) |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java` | `filterEntities(...)` | L2940–3004: For ENTITY_TYPE MONITOR and non-archived, L2959–2960: `items = ... getObjectIdsByIds(context.getJsonArray(ENTITIES)).stream()....filter(qualifiedObjects::contains)...`. Intersects context ENTITIES with qualifiedObjects. | Internal (used by qualifyEntities for visualization) |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java` | `qualifyEntities(...)` | L2503–2555: Calls filterEntities(context, userId, qualifiedObjects, ...); builds entities only from filtered items. | Internal |
| `motadata/src/main/java/com/mindarray/api/MetricPolicy.java` | (API handlers) | L121, L126, L135, L139: getItemsByUserProfile(principal.getLong(ID), ...) / getItemsByUserProfile(response.getLong(USER_ID), ...) for entity scoping. | API |
| `motadata/src/main/java/com/mindarray/api/Query.java` | `getObjects(RoutingContext)`, `getObjectsByTag`, etc. | L126, L148, L169 (per AUTHORITY_SURFACE_SCAN): getItemsByUserProfile used for some query paths. | API |

**Critical gap:**  
`motadata/src/main/java/com/mindarray/api/Query.java` — **getObjectsBySeverity** (L271–275) does **not** use getItemsByUserProfile. It returns `MetricPolicyCacheStore.getStore().getItemsBySeverity(severity)` directly.

---

## STEP 3 — Context Merge Points

### Context Merge Sites

| File | Method | What is merged | User filtering before vs after merge |
|------|--------|----------------|--------------------------------------|
| `motadata/src/main/java/com/mindarray/visualization/VisualizationManager.java` | (handler) | L460: `context = WidgetConfigStore.getStore().getItem(event.getLong(ID)).mergeIn(event)`. Widget config merged with request event. | Filtering applied **after** merge: downstream VisualizationEventManager/VisualizationMetricManager use qualifiedObjects and qualifyEntities when building ENTITIES for policy cache. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java` | (handler) | L580: `queryUIContexts.computeIfAbsent(..., value -> new JsonObject().mergeIn(event))`. L718: `queryContexts.put(..., new JsonObject().mergeIn(event)...)`. L815, 924, 979: `visualizationDataSource.put(ENTITIES, entities)` where `entities` comes from qualifyEntities/setEntities (user-scoped). | ENTITIES set from qualifiedEntities (which uses filterEntities with qualifiedObjects). Filtering applied **before** putting ENTITIES into visualizationDataSource for policy cache. |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationMetricManager.java` | (handler) | L1418: `subQueryContext = new JsonObject().mergeIn(event).put(...).put(ADMIN_ROLE, NO)...`. L927, 929, 942: entities/pluginEntities/entityGroups from qualifyEntities; L1473: `visualizationDataSource.put(ENTITIES, ObjectConfigStore.getStore().getItemsByObjectIds(entities.keySet()...))` — entities from qualified path. | Filtering applied **before** merge into subQueryContext/visualizationDataSource (qualifiedObjects at L694, qualifyEntities uses them). |
| `motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java` | (inventory join) | L3560: `userGroups = GroupConfigStore.getStore().getItemsByUserProfile(user.getLong(ID))`; L3514–3534: objects filtered by user group before adding to result. | Filtering applied when building result list; setSeverityColumns/setPolicyStats then called only for objects already in that filtered result. |
| `motadata/src/main/java/com/mindarray/policy/EventPolicyInspector.java` | (trigger context) | L1034: `.mergeIn(EventPolicyCacheStore.getStore().getTriggerTicks(policy.getLong(ID)))`. Policy/trigger data merged; no user filter in this path. | N/A (runbook/notification path; not policy→monitor list for UI). |

**Conclusion:** In the visualization path, ENTITIES passed to PolicyCacheService are built from qualifyEntities/filterEntities with qualifiedObjects, so filtering is applied **before** the merged context is used for policy cache. The merge of widget config + event does not bypass filtering for policy/alert widgets because ENTITIES are overwritten with qualified entities. **No merge point found that injects unfiltered monitor list into policy resolution for the described scenario.**

---

## STEP 4 — Policy Visibility Flow (Policy ID → Monitor IDs → Detail → Response)

| Stage | File / Method | Filtering applied? | Notes |
|-------|----------------|-------------------|--------|
| 1. Policy attached to monitors | Policy engine / MetricPolicyCacheStore.updateItem | N/A | Policy cache stores policy key by object id (`policyKeysByObject`). No user check. |
| 2. Request for “policy by group” / “active policies” / “heatmap” | VisualizationEventManager (L1392, 1404, 1456) | **YES** (upstream) | visualizationDataSource.ENTITIES set at L815/924/979 from `entities` built via qualifyEntities(..., qualifiedObjects, ...). qualifiedObjects from getObjectIdsByUserProfile at L607. |
| 3. Policy cache reads ENTITIES | PolicyCacheServiceImpl.getPolicyCounts / getMetricPolicies / buildHeatmapByObjects | **NO** | Uses context.getJsonArray(ENTITIES) as-is. No getItemsByUserProfile in PolicyCacheServiceImpl. |
| 4. MetricPolicyCacheStore returns policy data per entity | MetricPolicyCacheStore.getItems(entities) / getItemsByCategory(entities, ...) | **NO** | Returns data for every ID in `entities`. |
| 5. Response to UI (visualization path) | VisualizationConstants.send(... result ...) | **YES** (upstream) | Result is for ENTITIES that were already user-scoped in step 2. |
| 6. **Alternative path: Query API** | Query.getObjectsBySeverity (L271–275) | **NO** | Sends `MetricPolicyCacheStore.getStore().getItemsBySeverity(severity)` directly. No user/principal or getItemsByUserProfile. Any user can receive all objects (ID, name, IP, severity, object_id) for that severity. |

**Flow summary:**  
- **Visualization path:** Filtering is applied when building ENTITIES (qualifiedObjects → qualifyEntities → filterEntities). Policy resolution and response use that filtered set; no authority leak from policy→monitor resolution or merge in this path for the described scenario.  
- **Query API path:** getObjectsBySeverity returns all monitors in the given severity with no user filtering — **unfiltered retrieval path**.

---

## STEP 5 — Authority Leak Classification

### Answers (code-only)

1. **Is there any path where monitor details are retrieved without getItemsByUserProfile filtering?**  
   **Yes.**  
   - **Query.getObjectsBySeverity** (Query.java L271–275): returns `MetricPolicyCacheStore.getStore().getItemsBySeverity(severity)` to the client. Response includes ID, OBJECT_NAME, OBJECT_IP, SEVERITY, OBJECT_ID for every object in that severity. No getItemsByUserProfile or principal-based filter.  
   - **MetricPolicyCacheStore.getItemsBySeverity** (MetricPolicyCacheStore.java L813–831): iterates all `objects` with that severity and adds full object details; no user parameter.

2. **Is filtering applied only at UI layer but not in policy resolution?**  
   **Partially.**  
   - In the **visualization** path, filtering is applied when building the ENTITIES passed to policy cache (getObjectIdsByUserProfile → qualifiedObjects → qualifyEntities → filterEntities). So for visualization, policy resolution receives already-filtered ENTITIES.  
   - **Policy resolution itself** (PolicyCacheServiceImpl, MetricPolicyCacheStore) never applies getItemsByUserProfile; they trust the caller. So any **other** caller that passes unfiltered ENTITIES would get unfiltered policy/monitor data. The only such caller identified in code is the Query API (getObjectsBySeverity), which does not use ENTITIES but returns all objects by severity.

3. **Can policy resolution return monitor IDs outside the user’s group scope?**  
   **Yes, if the caller passes those IDs.**  
   - PolicyCacheServiceImpl and MetricPolicyCacheStore do not restrict by user; they return data for whatever ENTITIES or severity they are given.  
   - In the **visualization** path, ENTITIES are restricted by qualifyEntities/filterEntities, so policy resolution does not receive out-of-scope IDs there.  
   - In the **Query** path, getObjectsBySeverity returns all monitors in the given severity, so a user can see monitor details outside their group scope.

### Authority Leak Possibility

**Strong (unfiltered retrieval path exists)**

- **Unfiltered path:** `Query.getObjectsBySeverity` → `MetricPolicyCacheStore.getItemsBySeverity(severity)` returns full monitor details (ID, name, IP, severity, object_id) for every object in that severity with no user or group check.  
- Policy-to-monitor resolution and visualization merge paths use user-scoped ENTITIES when building context for policy cache; the leak is not from “policy resolution merging with unfiltered data” in the visualization flow but from a **separate API endpoint** that exposes all monitors by severity without authority checks.

---

## File → Method → Line Reference Summary

| Location | Method / site | Relevance |
|----------|----------------|-----------|
| Query.java | getObjectsBySeverity | L271–275: Unfiltered API response by severity. |
| MetricPolicyCacheStore.java | getItemsBySeverity | L813–831: Returns all objects for severity; no user filter. |
| MetricPolicyCacheStore.java | getItems(JsonArray entities) | L381–421: Returns policy items for given entities; no filter. |
| MetricPolicyCacheStore.java | getItemsByCategory(JsonArray entities, String category) | L423–467: Same; no filter. |
| PolicyCacheServiceImpl.java | getPolicyCounts | L382–447: Uses context ENTITIES; no getItemsByUserProfile. |
| PolicyCacheServiceImpl.java | getMetricPolicies | L483–489: getItems(context.getJsonArray(ENTITIES)); no filter. |
| PolicyCacheServiceImpl.java | buildHeatmapByObjects | L1117–1118, 1146–1166: getItems(ENTITIES) / getSeverity per entity; no filter. |
| PolicyCacheServiceImpl.java | buildHeatmapByApplications | L1204: getItems(ENTITIES); no filter. |
| VisualizationEventManager.java | EVENT_VISUALIZATION_EVENT consumer | L607, 609: getObjectIdsByUserProfile / getItemsByUserProfile → qualifiedObjects, qualifiedSources. |
| VisualizationEventManager.java | POLICY case, cache path | L805–816: qualifyEntities(..., qualifiedObjects, ...); setEntities; visualizationDataSource.put(ENTITIES, entities). |
| VisualizationMetricManager.java | EVENT_VISUALIZATION_METRIC consumer | L694: getObjectIdsByUserProfile → qualifiedObjects. |
| VisualizationConstants.java | filterEntities | L2959–2960: MONITOR + ENTITIES → filter by qualifiedObjects::contains. |
| VisualizationConstants.java | qualifyEntities | L2517: filterEntities(context, userId, qualifiedObjects, ...). |
| GroupConfigStore.java | getItemsByUserProfile(long) | L214–239. |
| ObjectConfigStore.java | getItemsByUserProfile(long), getObjectIdsByUserProfile(long) | L505–509, L594–605. |

---

*Findings are structural only; no phase classification or fix suggestions.*
