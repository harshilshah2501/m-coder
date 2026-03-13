# Phase 2: Artifact Extraction (Grounded Only)

## Artifact Inventory

### ARTIFACT-001: Anomaly Threshold Severity Evaluation

**File Path(s):**
- `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyInspector.java`

**Module:** `com.mindarray.policy.AIOpsMetricPolicyInspector`

**Decision Point:**
- Lines 346-372: Anomaly percentage calculation and severity threshold evaluation
- Exact location: `inspectAnomaly()` method, lines 339-372

**Code Context:**
```java
if (violations > 0)
{
    value = CommonUtil.getFloat((violations * 100) / rows.size());
    var conditions = policy.getJsonObject(POLICY_CONTEXT).getJsonObject(POLICY_SEVERITY);
    if (conditions != null)
    {
        for (var index = 0; index < POLICY_SEVERITIES.size(); index++)
        {
            var severity = POLICY_SEVERITIES.getString(index);
            var condition = conditions.getJsonObject(severity, null);
            if (condition != null && PolicyEngineConstants.evaluateCondition(Boolean.TRUE, condition.getString(POLICY_CONDITION), condition.getValue(POLICY_THRESHOLD), value))
            {
                result.put(VALUE, value);
                result.put(SEVERITY, Severity.valueOf(severity));
                result.put(POLICY_THRESHOLD, violations);
                break;
            }
        }
    }
}
```

**Signal Ambiguity:**
- Anomaly percentage calculation: `(violations * 100) / rows.size()` - ambiguity in whether a single anomaly point should trigger alert vs. requiring percentage threshold
- Severity threshold comparison: Multiple severity levels (CRITICAL, MAJOR, WARNING) evaluated in order - ambiguity in which severity level to assign when multiple thresholds are breached
- Boundary condition: When `violations > 0` but percentage is below all thresholds - should it be CLEAR or should there be a minimum threshold?

**Authority Surface:**
- Policy configuration: `policy.getJsonObject(POLICY_CONTEXT).getJsonObject(POLICY_SEVERITY)`
- Severity assignment affects alert routing and notification recipients
- Policy threshold values determine alert severity classification

**Irreversible Boundary:**
- **Exact phrase:** `result.put(SEVERITY, Severity.valueOf(severity));` followed by `processPolicyFlap()` call (line 288) which triggers `triggerAction()` (line 1135) which publishes `EVENT_NOTIFICATION` (line 1259)
- **Boundary type:** Contract Exposure
- **Boundary location:** Alert publication after severity determination

**Stress Surfaces:**
- Edge case: `violations = 1` with `rows.size() = 1000` → 0.1% anomaly rate - should this trigger?
- Multiple threshold breaches: If anomaly percentage breaches both MAJOR (10%) and CRITICAL (20%) thresholds simultaneously
- Zero violations but non-zero rows: Should result be CLEAR or UNKNOWN?

---

### ARTIFACT-002: Correlation Root Cause vs. Cascading Failure

**File Path(s):**
- `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java`

**Module:** `com.mindarray.aiops.AvailabilityCorrelationEngine`

**Decision Point:**
- Lines 710-744: Probe type handling and correlation initiation
- Lines 805-823: Object status update decision (DOWN vs. UNREACHABLE)
- Exact location: `discard()` method, lines 799-824

**Code Context:**
```java
if (ObjectStatusCacheStore.getStore().getItem(event.getLong(Metric.METRIC_OBJECT)).equalsIgnoreCase(STATUS_DOWN))
{
    var found = false;
    for (var entry : correlations.entrySet())
    {
        for (var probeEntry : entry.getValue().entrySet())
        {
            var context = probeEntry.getValue();
            if (context.get(AIOpsConstants.CORRELATED_UNREACHABLE_OBJECTS) != null && context.get(AIOpsConstants.CORRELATED_UNREACHABLE_OBJECTS).contains(event.getLong(Metric.METRIC_OBJECT)))
            {
                ObjectStatusCacheStore.getStore().updateItem(event.getLong(Metric.METRIC_OBJECT), STATUS_UNREACHABLE, DateTimeUtil.currentSeconds());
                found = true;
                break;
            }
        }
        if (found) break;
    }
}
```

**Signal Ambiguity:**
- Network topology vs. actual device failure: When a device is DOWN, is it because of upstream network failure (UNREACHABLE) or actual device failure (DOWN)?
- Dependency graph traversal: How far upstream should correlation traverse to find root cause?
- Timing ambiguity: Multiple devices going down simultaneously - which is the root cause?

**Authority Surface:**
- Correlation graph state: `correlations` map (line 92)
- Object status cache: `ObjectStatusCacheStore.updateItem()` (line 813)
- Dependency mapper: Dependency relationships affect correlation traversal

**Irreversible Boundary:**
- **Exact phrase:** `ObjectStatusCacheStore.getStore().updateItem(event.getLong(Metric.METRIC_OBJECT), STATUS_UNREACHABLE, DateTimeUtil.currentSeconds());` (line 813) followed by correlation file persistence (line 443)
- **Boundary type:** Organizational Commitment
- **Boundary location:** Object status update and correlation state persistence

**Stress Surfaces:**
- Circular dependencies: Device A depends on B, B depends on A - which is root cause?
- Partial network failure: Some paths down, others up - correlation ambiguity
- Rapid state changes: Device goes DOWN then UP then DOWN again - correlation state consistency

---

### ARTIFACT-003: Policy Suppression Logic

**File Path(s):**
- `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyManager.java`

**Module:** `com.mindarray.policy.AIOpsMetricPolicyManager`

**Decision Point:**
- Lines 474-503: Policy suppression/unsuppression handling
- Lines 191: Suppression check in policy qualification
- Exact location: `EVENT_CHANGE_NOTIFICATION` handler, `SUPPRESS_POLICY` case (lines 474-486)

**Code Context:**
```java
case SUPPRESS_POLICY ->
{
    if (message.body() != null && event.containsKey(ENTITY_ID) && policies.containsKey(event.getLong(POLICY_ID)))
    {
        var objectId = event.getLong(ENTITY_ID);
        if (!suppressedPolicies.containsKey(objectId))
        {
            suppressedPolicies.put(objectId, new HashSet<>());
        }
        suppressedPolicies.get(objectId).add(event.getLong(POLICY_ID));
    }
}
```

**Signal Ambiguity:**
- False positive vs. legitimate alert: When should a policy be suppressed? Manual suppression vs. automatic suppression based on conditions?
- Suppression scope: Should suppression apply to all instances of an object or specific instances?
- Suppression duration: Temporary suppression vs. permanent suppression - when does suppression expire?

**Authority Surface:**
- Suppression state: `suppressedPolicies` map (line 97)
- Policy evaluation: Suppression check affects whether policy is evaluated (line 191)
- UI alert visibility: Suppressed policies don't generate alerts

**Irreversible Boundary:**
- **Exact phrase:** `suppressedPolicies.get(objectId).add(event.getLong(POLICY_ID));` (line 485) which prevents policy evaluation and alert generation
- **Boundary type:** Contract Exposure
- **Boundary location:** Suppression state prevents alert publication

**Stress Surfaces:**
- Suppression during active alert: Should suppression clear existing alerts or only prevent new ones?
- Suppression race condition: Policy triggers while suppression is being applied
- Suppression inheritance: Should suppression apply to correlated objects?

---

### ARTIFACT-004: Runbook Execution Trigger Decision

**File Path(s):**
- `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java`

**Module:** `com.mindarray.policy.PolicyEngineConstants`

**Decision Point:**
- Lines 1391-1410: Runbook execution trigger logic
- Exact location: `triggerAction()` method, runbook branch (lines 1394-1410)

**Code Context:**
```java
severity = policy.getString(POLICY_TYPE).equalsIgnoreCase(PolicyType.AVAILABILITY.getName()) && context.containsKey(INSTANCE) && !context.getString(INSTANCE).isEmpty() ? (severity.equalsIgnoreCase(Severity.CRITICAL.name()) ? Severity.DOWN.name() : severity) : severity;

if (actions != null && actions.getJsonObject(PolicyTriggerActionType.RUNBOOK.getName()) != null && !actions.getJsonObject(PolicyTriggerActionType.RUNBOOK.getName()).isEmpty()
        && actions.getJsonObject(PolicyTriggerActionType.RUNBOOK.getName()).containsKey(severity) && !actions.getJsonObject(PolicyTriggerActionType.RUNBOOK.getName()).getJsonArray(severity).isEmpty())
{
    try
    {
        var entries = actions.getJsonObject(PolicyTriggerActionType.RUNBOOK.getName()).getJsonArray(severity);
        for (var index = 0; index < entries.size(); index++)
        {
            Bootstrap.vertx().eventBus().send(EventBusConstants.EVENT_RUNBOOK, prepareContext(entries.getJsonObject(index).getLong(ID), context, entityId, policy));
        }
    }
    catch (Exception exception)
    {
        logger.error(exception);
    }
}
```

**Signal Ambiguity:**
- Automated fix safety vs. manual review necessity: When should runbooks execute automatically vs. requiring manual approval?
- Severity mapping: Availability policies map CRITICAL to DOWN for runbook execution - is this correct?
- Multiple runbooks: When multiple runbooks are configured for same severity, should all execute or only first?

**Authority Surface:**
- Runbook execution: `EVENT_RUNBOOK` event bus message (line 1403)
- Target system state: Runbook execution affects SSH commands, API calls, etc.
- Worklog persistence: Runbook execution creates audit trail

**Irreversible Boundary:**
- **Exact phrase:** `Bootstrap.vertx().eventBus().send(EventBusConstants.EVENT_RUNBOOK, prepareContext(...));` (line 1403)
- **Boundary type:** Automation Execution
- **Boundary location:** Runbook execution initiation - cannot un-execute commands on target systems

**Stress Surfaces:**
- Runbook failure: What if runbook execution fails mid-way? Partial execution state
- Concurrent runbooks: Multiple runbooks executing simultaneously on same target
- Runbook dependency: Runbook A must complete before Runbook B - ordering ambiguity

---

### ARTIFACT-005: Baseline Window Selection and Object Creation Time Validation

**File Path(s):**
- `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyManager.java`

**Module:** `com.mindarray.policy.AIOpsMetricPolicyManager`

**Decision Point:**
- Lines 1058-1079: Baseline policy evaluation window and object creation time validation
- Exact location: `executeQuery()` method, baseline policy branch (lines 1058-1079)

**Code Context:**
```java
else if (policy.getString(POLICY_TYPE).equalsIgnoreCase(PolicyType.BASELINE.getName()))
{
    timeline = VisualizationConstants.VisualizationTimeline.LAST_15_DAYS.getName();
    context.put(VisualizationConstants.VISUALIZATION_CATEGORY, VisualizationConstants.VisualizationCategory.BASELINE.getName());
    context.put(VisualizationConstants.VISUALIZATION_GRANULARITY, "30 m");
    var iterator = value.iterator();
    while (iterator.hasNext())
    {
        var object = ObjectConfigStore.getStore().getItem(iterator.next());
        if ((DateTimeUtil.currentSeconds() - object.getLong(AIOpsObject.OBJECT_CREATION_TIME_SECONDS)) < BASELINE_TRIGGER_INTERVAL_SECONDS)
        {
            iterator.remove();
        }
    }
    context.put(VisualizationConstants.VISUALIZATION_RESULT_TYPE, VisualizationConstants.VisualizationResultType.COMPACTED.getName());
}
```

**Signal Ambiguity:**
- Baseline window selection: Why `LAST_15_DAYS`? Should it be configurable per policy?
- Object creation time threshold: `BASELINE_TRIGGER_INTERVAL_SECONDS` - why this specific duration? What if object was created 14 days ago?
- Granularity selection: `30 m` granularity - is this optimal for all metric types?

**Authority Surface:**
- Baseline parameters: Window, granularity affect future baseline calculations
- Policy evaluation: Objects removed from evaluation if creation time < threshold
- Future anomaly detection: Baseline affects future anomaly scoring accuracy

**Irreversible Boundary:**
- **Exact phrase:** Baseline query execution affects future baseline calculations, but boundary is at baseline parameter update affecting future scoring (indirect)
- **Boundary type:** Organizational Commitment
- **Boundary location:** Baseline parameters affecting future anomaly detection accuracy

**Stress Surfaces:**
- New object with historical data: Object created yesterday but has 30 days of historical data - should baseline use all data?
- Baseline recalculation: When should baseline be recalculated? On every evaluation or periodically?
- Seasonal variations: Baseline calculated during peak season vs. off-season - accuracy differences

---

### ARTIFACT-006: Alert Recipient Selection and Access Rights Filtering

**File Path(s):**
- `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java`
- `motadata/src/main/java/com/mindarray/policy/SeverityChangeEventProcessor.java`

**Module:** `com.mindarray.policy.PolicyEngineConstants`, `com.mindarray.policy.SeverityChangeEventProcessor`

**Decision Point:**
- Lines 1214+: Recipient selection in `triggerAction()` method
- Line 219 in SeverityChangeEventProcessor: User access rights filtering
- Exact location: `setRecipients()` calls and `filterNotifications()` method

**Code Context:**
```java
// In PolicyEngineConstants.triggerAction()
setRecipients(emailRecipients, smsRecipients, notificationContext.getJsonObject(Notification.NotificationType.EMAIL.getName()).getJsonArray(severity),context.getLong(ENTITY_ID));

// In SeverityChangeEventProcessor.filterNotifications()
filterNotifications(notificationCounts.get(userId), true, ObjectConfigStore.getStore().getObjectIdsByUserProfile(userId)).onComplete(result ->
{
    if (result.succeeded())
    {
        EventBusConstants.publish(event.getString(SESSION_ID), EventBusConstants.EVENT_ACTIVE_NOTIFICATION_QUERY, new JsonObject().put(STATUS, STATUS_SUCCEED).put(RESULT, result.result()));
    }
});
```

**Signal Ambiguity:**
- Alert priority vs. recipient access rights: Should high-severity alerts bypass access rights checks?
- Recipient selection: Policy-defined recipients vs. user profile recipients - which takes precedence?
- Notification channel selection: Email vs. SMS vs. Teams - who gets which channel?

**Authority Surface:**
- External notification systems: Email/SMS/Teams/Slack APIs
- User access rights: `ObjectConfigStore.getStore().getObjectIdsByUserProfile(userId)`
- Notification delivery: External systems cannot un-send notifications

**Irreversible Boundary:**
- **Exact phrase:** `Bootstrap.vertx().eventBus().<JsonObject>request(EventBusConstants.EVENT_NOTIFICATION, ...)` (line 1259, 1288) for email/SMS, `Notification.send()` (line 1375) for Teams/Slack
- **Boundary type:** Contract Exposure
- **Boundary location:** External notification dispatch - cannot un-send messages

**Stress Surfaces:**
- Access rights change: User loses access after notification sent - should notification be revoked?
- Notification failure: Partial delivery (some recipients receive, others don't) - state consistency
- Recipient list changes: Policy updated while notification in-flight - which recipients get notified?

---

### ARTIFACT-007: Policy Flap Detection and Trigger Decision

**File Path(s):**
- `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java`

**Module:** `com.mindarray.policy.PolicyEngineConstants`

**Decision Point:**
- Lines 991-1011: Policy flap detection logic
- Lines 1132-1143: Trigger decision based on previous severity
- Exact location: `processPolicyFlap()` method (lines 971-1150)

**Code Context:**
```java
if (triggeredPolicies.containsKey(policyKey))
{
    var triggeredContext = triggeredPolicies.get(policyKey);
    if (!triggeredContext.getString(SEVERITY).equalsIgnoreCase(severity))
    {
        trigger = true;
    }
    previousSeverity = triggeredContext.getString(SEVERITY);
    context = triggeredContext.mergeIn(context);
}
else
{
    if (!clearSeverity)
    {
        trigger = true;
    }
}

// Later in method:
if (previousSeverity.equalsIgnoreCase(EMPTY_VALUE) || !previousSeverity.equalsIgnoreCase(Severity.UNREACHABLE.name()))
{
    triggerAction(severity, trigger, policy, context, ...);
}
else
{
    logger.trace(String.format("Not triggering action for %s ", objectName));
}
```

**Signal Ambiguity:**
- Severity change detection: When severity changes from CRITICAL to MAJOR, should this trigger action or only severity escalation?
- UNREACHABLE handling: Why are actions not triggered when previous severity was UNREACHABLE?
- Clear severity: First-time CLEAR severity doesn't trigger - but what if object was never monitored before?

**Authority Surface:**
- Policy state: `triggeredPolicies` map (line 1023)
- Action triggering: `triggerAction()` call (line 1135)
- Alert publication: Actions trigger notifications and runbooks

**Irreversible Boundary:**
- **Exact phrase:** `triggerAction(severity, trigger, policy, context, ...);` (line 1135) which leads to notification dispatch
- **Boundary type:** Contract Exposure
- **Boundary location:** Action triggering leads to external notification dispatch

**Stress Surfaces:**
- Rapid severity changes: CRITICAL → CLEAR → CRITICAL in quick succession - should all trigger?
- UNREACHABLE → CRITICAL transition: Why skip action trigger?
- Policy state corruption: `triggeredPolicies` map inconsistent - how to recover?

---

### ARTIFACT-008: Correlation Duplicate Request Detection

**File Path(s):**
- `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java`

**Module:** `com.mindarray.aiops.AvailabilityCorrelationEngine`

**Decision Point:**
- Lines 623-670: Duplicate correlation request detection
- Lines 749-758: Running probe check
- Exact location: Event handler, duplicate detection logic (lines 623-670)

**Code Context:**
```java
if (!probes.contains(id))
{
    // Check if object already correlated
    vertx.eventBus().<JsonArray>request(config().getString(EVENT_TYPE) + EVENT_QUERY,
            new JsonObject().put(EVENT_QUERY_BULK, YES).put(AIOpsConstants.CORRELATED_OBJECT_QUERY, YES),
            deliveryOptions, reply ->
            {
                if (reply.succeeded())
                {
                    var result = reply.result().body();
                    if (!result.contains(id))
                    {
                        if (!downObjects.containsKey(id) || (!downObjects.get(id).contains(instance)))
                        {
                            promise.complete(true);
                        }
                        else
                        {
                            promise.complete(false);
                            discard(event, key, String.format("duplicate request found with key : %s", key), STATUS_FAIL);
                        }
                    }
                    else
                    {
                        promise.complete(false);
                        if (correlations.containsKey(key) && correlations.get(key).containsKey(probeType))
                        {
                            discard(event, key, String.format("%s already correlated", event.getString(AIOpsObject.OBJECT_NAME)), STATUS_FAIL);
                        }
                        else
                        {
                            discard(event, key, String.format("%s already correlated", event.getString(AIOpsObject.OBJECT_NAME)), STATUS_ABORT);
                        }
                    }
                }
            });
}
```

**Signal Ambiguity:**
- Duplicate detection timing: What if correlation completes between duplicate check and correlation start?
- Instance-level vs. object-level: Duplicate check for instance but correlation for object - ambiguity
- STATUS_FAIL vs. STATUS_ABORT: When to use which status code?

**Authority Surface:**
- Correlation state: `correlations` map, `runningProbes` map, `downObjects` map
- Object status: Status updates affect UI display
- Correlation persistence: Duplicate detection affects correlation graph state

**Irreversible Boundary:**
- **Exact phrase:** `discard(event, key, ..., STATUS_FAIL/STATUS_ABORT);` (lines 651, 664, 668) which updates object status cache (line 813) and publishes reply (line 828)
- **Boundary type:** Contract Exposure
- **Boundary location:** Status update and event publication

**Stress Surfaces:**
- Race condition: Two correlation requests arrive simultaneously - both pass duplicate check
- Correlation completion: Correlation completes while duplicate check in progress
- Status inconsistency: Object marked as DOWN but correlation says UNREACHABLE

---

### ARTIFACT-009: Forecast Policy Time-to-Breach Calculation

**File Path(s):**
- `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyInspector.java`

**Module:** `com.mindarray.policy.AIOpsMetricPolicyInspector`

**Decision Point:**
- Lines 404-471: Forecast policy evaluation and time-to-breach calculation
- Exact location: `inspectForecast()` method (lines 404-471)

**Code Context:**
```java
for (var i = 0; i < records.size(); i++)
{
    var record = records.getJsonObject(i);
    var value = record.getValue(event.getString(METRIC));
    if (PolicyEngineConstants.evaluateCondition(Boolean.TRUE, condition.getString(POLICY_CONDITION), threshold, value))
    {
        if (record.getLong(TIME_STAMP) <= System.currentTimeMillis())
        {
            trigger = false;
        }
        else
        {
            result.put(VALUE, DateTimeUtil.millisToDuration(record.getLong(TIME_STAMP) - System.currentTimeMillis()));
            result.put(SEVERITY, Severity.valueOf(severity));
            result.put(POLICY_THRESHOLD, condition.getString(POLICY_THRESHOLD));
        }
        break;
    }
}
```

**Signal Ambiguity:**
- Time-to-breach calculation: `record.getLong(TIME_STAMP) - System.currentTimeMillis()` - what if forecast timestamp is in past?
- Threshold already breached: `record.getLong(TIME_STAMP) <= System.currentTimeMillis()` sets `trigger = false` - should this trigger CLEAR or different severity?
- Forecast accuracy: Forecasted values may be inaccurate - should policy trigger based on predictions?

**Authority Surface:**
- Forecast data: Prediction results from visualization engine
- Policy severity: Severity assignment affects alert routing
- Time-to-breach: Duration affects urgency and notification priority

**Irreversible Boundary:**
- **Exact phrase:** `result.put(SEVERITY, Severity.valueOf(severity));` (line 449) followed by `processPolicyFlap()` call (line 288) which triggers notifications
- **Boundary type:** Contract Exposure
- **Boundary location:** Alert publication based on forecast predictions

**Stress Surfaces:**
- Forecast inaccuracy: Forecast predicts breach but actual doesn't occur - false positive
- Past timestamps: Forecast timestamp in past but threshold not yet breached - timing ambiguity
- Multiple breach points: Multiple forecast points breach threshold - which time-to-breach to use?

---

### ARTIFACT-010: Baseline Deviation Calculation and Threshold Comparison

**File Path(s):**
- `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyInspector.java`

**Module:** `com.mindarray.policy.AIOpsMetricPolicyInspector`

**Decision Point:**
- Lines 482-533: Baseline policy evaluation
- Lines 546-560: Threshold calculation (absolute vs. relative)
- Exact location: `inspect()` method for baseline (lines 482-533)

**Code Context:**
```java
var metricValue = event.getValue(event.getString(METRIC) + CARET_SEPARATOR + DatastoreConstants.AggregationType.AVG.getName() + CARET_SEPARATOR + "baseline");
var value = event.getValue(event.getString(METRIC) + CARET_SEPARATOR + DatastoreConstants.AggregationType.AVG.getName());
var context = policy.getJsonObject(POLICY_CONTEXT);
if (context != null)
{
    var conditions = context.getJsonObject(POLICY_SEVERITY);
    if (conditions != null)
    {
        for (var index = 0; index < POLICY_SEVERITIES.size(); index++)
        {
            var severity = POLICY_SEVERITIES.getString(index);
            var condition = conditions.getJsonObject(severity, null);
            if (condition != null)
            {
                var threshold = calculateThreshold(condition.getString(POLICY_CONDITION), conditions.getJsonObject(severity, null), metricValue, context.getString(THRESHOLD_TYPE, ThresholdType.RELATIVE.getName()));
                if (PolicyEngineConstants.evaluateCondition(Boolean.TRUE, condition.getString(POLICY_CONDITION), threshold, value))
                {
                    result.put(VALUE, value);
                    result.put(SEVERITY, Severity.valueOf(severity));
                    result.put(POLICY_THRESHOLD, threshold);
                    break;
                }
            }
        }
    }
}
```

**Signal Ambiguity:**
- Baseline value selection: Which baseline value to use? Average, median, percentile?
- Threshold type: Absolute vs. relative threshold calculation - when to use which?
- Deviation direction: "above" vs. "below" baseline - how to handle bidirectional deviations?

**Authority Surface:**
- Baseline parameters: Baseline calculation affects threshold comparison
- Policy severity: Severity assignment affects alert routing
- Threshold calculation: Absolute vs. relative affects sensitivity

**Irreversible Boundary:**
- **Exact phrase:** `result.put(SEVERITY, Severity.valueOf(severity));` (line 512) followed by `processPolicyFlap()` call (line 288)
- **Boundary type:** Contract Exposure
- **Boundary location:** Alert publication based on baseline deviation

**Stress Surfaces:**
- Baseline drift: Baseline calculated during different operational conditions - accuracy over time
- Small baseline values: Relative threshold on small baseline values - percentage vs. absolute impact
- Baseline update frequency: When should baseline be recalculated? On every evaluation or periodically?

---

### ARTIFACT-011: Correlation Graph Persistence Decision

**File Path(s):**
- `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java`

**Module:** `com.mindarray.aiops.AvailabilityCorrelationEngine`

**Decision Point:**
- Lines 380-472: Correlation state persistence to disk
- Exact location: Event bus consumer for `.write` operation (lines 380-472)

**Code Context:**
```java
vertx.eventBus().<byte[]>localConsumer(config().getString(EventBusConstants.EVENT_TYPE) + ".write", message ->
{
    if (!writePending)
    {
        writePending = true;
        var items = new HashMap<>();
        if (!correlations.isEmpty())
        {
            items.put("correlations", correlations);
        }
        if (!runningProbes.isEmpty())
        {
            // ... check if updated ...
            if (updated)
            {
                items.put("running.probes", runningProbes);
            }
        }
        if (!downObjects.isEmpty())
        {
            items.put("down.objects", downObjects);
        }
        vertx.<byte[]>executeBlocking(promise ->
        {
            byte[] bytes = null;
            try
            {
                if (!items.isEmpty())
                {
                    bytes = CodecUtil.serialize(items);
                    bytes = CodecUtil.compress(bytes);
                    vertx.fileSystem().writeFileBlocking(CURRENT_DIR + PATH_SEPARATOR + CONFIG_DIR + PATH_SEPARATOR + config().getString(EVENT_ROUTER_CONFIG), Buffer.buffer(bytes));
                }
            }
            catch (Exception exception)
            {
                LOGGER.error(exception);
            }
            promise.complete(bytes);
        }, false, result ->
        {
            message.reply(result.result());
            writePending = false;
        });
    }
});
```

**Signal Ambiguity:**
- Persistence frequency: When should correlation state be persisted? On every change or periodically?
- Partial persistence: What if only `correlations` map has changes but `runningProbes` is empty - should we persist?
- Write failure handling: What if file write fails? Should correlation state be lost or retried?

**Authority Surface:**
- File system: Persistent storage affects system restart recovery
- Correlation state: Persisted state affects future correlation decisions
- System recovery: Persisted state used to restore correlation state after restart

**Irreversible Boundary:**
- **Exact phrase:** `vertx.fileSystem().writeFileBlocking(..., Buffer.buffer(bytes));` (line 443)
- **Boundary type:** Organizational Commitment
- **Boundary location:** File persistence makes correlation state persistent across restarts

**Stress Surfaces:**
- Write failure: File system full or permission denied - correlation state lost?
- Concurrent writes: Multiple correlation engines writing simultaneously - file corruption?
- State inconsistency: Memory state vs. persisted state mismatch after restart

---

### ARTIFACT-012: Policy Qualification and Object/Group/Tag Matching

**File Path(s):**
- `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyManager.java`

**Module:** `com.mindarray.policy.AIOpsMetricPolicyManager`

**Decision Point:**
- Lines 680-794: Policy qualification logic (`qualify()` method)
- Lines 825-880: Policy assignment logic (`assign()` method)
- Exact location: `qualify()` method (lines 680-794)

**Code Context:**
```java
private Map<String, List<Long>> qualify(JsonArray groups, JsonArray tags, long objectId, int pluginId)
{
    var qualifiedPolicies = new HashMap<String, List<Long>>();
    // Check policiesByObject
    if (policiesByObject.containsKey(objectId))
    {
        // ... add policies ...
    }
    // Check policiesByGroup
    for (var index = 0; index < groups.size(); index++)
    {
        var group = groups.getLong(index);
        if (policiesByGroup.containsKey(group))
        {
            // ... add policies ...
        }
    }
    // Check policiesByTag
    for (var index = 0; index < tags.size(); index++)
    {
        var tagId = tags.getLong(index);
        if (policiesByTag.containsKey(tagId))
        {
            // ... add policies ...
        }
    }
    // Sort by creation time if multiple policies match
    if (sort)
    {
        entry.getValue().sort(Comparator.comparing(item -> this.policies.get(CommonUtil.getLong(item)).getLong(POLICY_CREATION_TIME)).reversed());
    }
    return qualifiedPolicies;
}
```

**Signal Ambiguity:**
- Policy precedence: Object-level vs. group-level vs. tag-level policies - which takes precedence?
- Multiple policy matching: When multiple policies match, which one is evaluated? (Sorted by creation time, newest first)
- Plugin compatibility: Policy qualification checks plugin compatibility - what if policy applies to multiple plugins?

**Authority Surface:**
- Policy evaluation: Qualification determines which policies are evaluated
- Policy assignment: Assignment logic affects policy-to-object mapping
- Policy precedence: Newest policy takes precedence when multiple match

**Irreversible Boundary:**
- **Exact phrase:** Policy qualification affects which policies are evaluated, but boundary is at policy evaluation triggering alert publication
- **Boundary type:** Organizational Commitment (indirect)
- **Boundary location:** Policy qualification affects future policy evaluation decisions

**Stress Surfaces:**
- Policy conflicts: Object-level policy says CRITICAL at 80%, group-level says MAJOR at 80% - which applies?
- Policy updates: Policy updated while qualification in progress - which version is used?
- Tag changes: Object tags change - should policy qualification be re-evaluated?

---

## Artifact Summary

| Artifact ID | Category | Decision Point | Irreversible Boundary | Boundary Type |
|-------------|----------|----------------|----------------------|----------------|
| ARTIFACT-001 | Threshold Changes | Anomaly severity evaluation | Alert publication | Contract Exposure |
| ARTIFACT-002 | Correlation Updates | Root cause vs. cascading failure | Status update + correlation persistence | Organizational Commitment |
| ARTIFACT-003 | Suppression Logic | Policy suppression decision | Suppression prevents alert | Contract Exposure |
| ARTIFACT-004 | Automation Enablement | Runbook execution trigger | Runbook execution initiation | Automation Execution |
| ARTIFACT-005 | Baseline Logic | Baseline window selection | Baseline parameters affect future scoring | Organizational Commitment |
| ARTIFACT-006 | Alert Routing | Recipient selection | External notification dispatch | Contract Exposure |
| ARTIFACT-007 | Policy Flap | Flap detection and trigger | Action triggering | Contract Exposure |
| ARTIFACT-008 | Correlation Duplicate | Duplicate request detection | Status update + event publication | Contract Exposure |
| ARTIFACT-009 | Forecast Policy | Time-to-breach calculation | Alert publication based on forecast | Contract Exposure |
| ARTIFACT-010 | Baseline Deviation | Baseline threshold comparison | Alert publication based on deviation | Contract Exposure |
| ARTIFACT-011 | Correlation Persistence | Correlation graph persistence | File persistence | Organizational Commitment |
| ARTIFACT-012 | Policy Qualification | Policy matching logic | Policy qualification affects evaluation | Organizational Commitment (indirect) |
