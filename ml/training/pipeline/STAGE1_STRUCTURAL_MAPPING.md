# Phase 1: Repository Structural Mapping

## Architecture Flow Map

```
Signal Ingestion
    ↓
Baseline Computation
    ↓
Anomaly Detection
    ↓
Correlation Engine
    ↓
Alert Publication
    ↓
Automation / Remediation
```

## Stage Analysis

### 1. Signal Ingestion

**Entry Points:**
- `AIOpsMetricPolicyManager.updateContext()` (line 524) - receives metric events via EventBus
- EventBus listener: `EVENT_DATASTORE_FLUSH` (line 368)
- EventBus listener: `EVENT_CHANGE_NOTIFICATION` (line 400)

**Module:** `com.mindarray.policy.AIOpsMetricPolicyManager`
**File:** `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyManager.java`

**Control Surface:**
- EventBus message handlers
- Policy qualification logic (`qualify()` method, line 680)
- Instance-level metric inspection (`inspectInstanceMetric()`, line 588)

**Exit Points:**
- Qualified policies forwarded to `executeQuery()` (line 205)
- Policy inspection events sent to `EVENT_AIOPS_METRIC_POLICY` (line 302)

**External State Writes:** None (read-only event processing)

**Feature Flag Gates:** None identified

**Permission Checks:** None at this stage

**Where State Becomes Externally Visible:** N/A (internal processing only)

**Where Rollback Becomes Non-Unilateral:** N/A (no external state changes)

---

### 2. Baseline Computation

**Entry Points:**
- `AIOpsMetricPolicyManager.executeQuery()` (line 1023) - baseline policy evaluation
- Periodic timer trigger (line 156)

**Module:** `com.mindarray.policy.AIOpsMetricPolicyManager`
**File:** `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyManager.java`

**Control Surface:**
- Visualization queries with `VISUALIZATION_CATEGORY.BASELINE` (line 1062)
- Timeline selection: `LAST_15_DAYS` (line 1060)
- Granularity: `30 m` (line 1064)
- Object creation time validation (lines 1072-1076)

**Exit Points:**
- Results sent to `EVENT_AIOPS_METRIC_POLICY_RESPONSE` (line 228)
- Response handler processes baseline results (lines 315-324)

**External State Writes:** None (read-only queries to visualization/datastore)

**Feature Flag Gates:** None identified

**Permission Checks:** None at this stage

**Where State Becomes Externally Visible:** N/A (computation only)

**Where Rollback Becomes Non-Unilateral:** N/A (no external state changes)

---

### 3. Anomaly Detection

**Entry Points:**
- `AIOpsMetricPolicyInspector.inspectAnomaly()` (line 317)
- Triggered via `EVENT_AIOPS_METRIC_POLICY` event bus message

**Module:** `com.mindarray.policy.AIOpsMetricPolicyInspector`
**File:** `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyInspector.java`

**Control Surface:**
- Anomaly percentage calculation: `(violations * 100) / rows.size()` (line 349)
- Severity threshold evaluation (lines 351-372)
- Condition evaluation via `PolicyEngineConstants.evaluateCondition()` (line 339)

**Exit Points:**
- Results sent to `processPolicyFlap()` (line 288)
- Policy flap processing triggers actions

**External State Writes:** None (computation only)

**Feature Flag Gates:** None identified

**Permission Checks:** None at this stage

**Where State Becomes Externally Visible:** N/A (computation only)

**Where Rollback Becomes Non-Unilateral:** N/A (no external state changes)

---

### 4. Correlation Engine

**Entry Points:**
- `AvailabilityCorrelationEngine.start()` - event bus consumer (line 125)
- Event handler: `setEventHandler(event -> ...)` (line 570)
- Event type: `EVENT_AVAILABILITY_CORRELATION`

**Module:** `com.mindarray.aiops.AvailabilityCorrelationEngine`
**File:** `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java`

**Control Surface:**
- Correlation map updates: `correlations` (line 92), `runningProbes` (line 94), `downObjects` (line 96)
- Probe type handling: `OBJECT_DOWN`, `INSTANCE_DOWN`, `OBJECT_UP`, `INSTANCE_UP` (lines 712-744)
- Dependency graph traversal via `runCorrelation()` method
- Ping status check: `checkPingStatus()` (line 576)

**Exit Points:**
- Correlation results published via `replyTopic` event bus (line 127)
- Correlation completion via `complete()` method (line 888)

**External State Writes:**
1. **File Persistence:** `config().getString(EVENT_ROUTER_CONFIG)` serialization (lines 380-472)
   - Location: `CURRENT_DIR + PATH_SEPARATOR + CONFIG_DIR + PATH_SEPARATOR + config().getString(EVENT_ROUTER_CONFIG)`
   - Method: `vertx.fileSystem().writeFileBlocking()` (line 443)
   - Content: Serialized correlations, runningProbes, downObjects maps
   - **IRREVERSIBLE BOUNDARY:** File write to disk (line 443)

2. **Cache Updates:** `ObjectStatusCacheStore.updateItem()` (line 273, line 813)
   - Updates object status to `STATUS_UNREACHABLE` or `STATUS_UNKNOWN`
   - **IRREVERSIBLE BOUNDARY:** Cache state update affects UI visibility

3. **Metric State Changes:** `enableMetric()` / `suspendMetric()` calls (via event bus)
   - Affects future data collection
   - **IRREVERSIBLE BOUNDARY:** Metric state change affects future policy evaluation

**Event Publication Points:**
- `vertx.eventBus().send(replyTopic, event)` - correlation results (line 828)
- `EVENT_CHANGE_NOTIFICATION` - correlation state changes

**Feature Flag Gates:** None identified

**Permission Checks:** None at this stage

**Where State Becomes Externally Visible:**
- File persistence makes correlation state persistent across restarts
- Cache updates affect UI object status display
- Metric state changes affect data collection pipeline

**Where Rollback Becomes Non-Unilateral:**
- File persistence requires file system access to rollback
- Cache updates require cache store coordination
- Metric state changes require event bus coordination

---

### 5. Alert Publication

**Entry Points:**
- `PolicyEngineConstants.processPolicyFlap()` (line 971)
- Triggered from policy inspectors after evaluation

**Module:** `com.mindarray.policy.PolicyEngineConstants`
**File:** `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java`

**Control Surface:**
- `triggerAction()` method (line 1186)
- Policy state tracking: `triggeredPolicies` map, `policyTimerContexts` map
- Severity determination and flap detection
- Auto-clear timer management (line 1037)
- Re-notification timer management (line 1043)

**Exit Points:**
- Notifications sent to external systems via `EVENT_NOTIFICATION` (line 1259, 1288, 1478, 1504)
- UI notifications via `EVENT_POLICY_NOTIFICATION` (SeverityChangeEventProcessor line 258)
- Real-time UI updates via `EVENT_SEVERITY_QUERY`

**External State Writes:**
1. **Policy Cache:** `MetricPolicyCacheStore.updateItem()` (line 1017)
   - Updates policy trigger state
   - **IRREVERSIBLE BOUNDARY:** Policy state persistence affects UI alert visibility

2. **Action Event Logging:** `writeTriggeredActionEvent()` calls
   - Logs notification/runbook execution events
   - **IRREVERSIBLE BOUNDARY:** Event log persistence

**Event Publication Points:**
1. **Email Notifications:** `EVENT_NOTIFICATION` with `NotificationType.EMAIL` (lines 1259, 1478)
   - **IRREVERSIBLE BOUNDARY:** External email dispatch (line 1259, 1478)

2. **SMS Notifications:** `EVENT_NOTIFICATION` with `NotificationType.SMS` (lines 1288, 1504)
   - **IRREVERSIBLE BOUNDARY:** External SMS dispatch (line 1288, 1504)

3. **Channel Notifications:** Teams/Slack via `Notification.send()` (lines 1375, 1560)
   - **IRREVERSIBLE BOUNDARY:** External channel notification dispatch

4. **UI Notifications:** `EVENT_POLICY_NOTIFICATION` (SeverityChangeEventProcessor line 258)
   - **IRREVERSIBLE BOUNDARY:** UI state update, user notification visibility

5. **Integration Events:** `EVENT_INTEGRATION` (line 1425)
   - **IRREVERSIBLE BOUNDARY:** External integration system notification

**Feature Flag Gates:** 
- `MotadataConfigUtil.devMode()` check (lines 1246, 1465) - affects notification delivery method

**Permission Checks:** 
- User access rights filtering in `SeverityChangeEventProcessor.filterNotifications()` (line 219)

**Where State Becomes Externally Visible:**
- Email/SMS/Teams/Slack notifications sent to external systems
- UI notifications visible to users
- Policy cache updates affect alert widget display
- Integration events sent to external ticketing/monitoring systems

**Where Rollback Becomes Non-Unilateral:**
- External notification systems (email/SMS/Teams/Slack) - cannot un-send notifications
- UI state requires user interaction to clear
- Integration systems require API coordination to rollback
- Policy cache requires cache store coordination

---

### 6. Automation / Remediation

**Entry Points:**
- `PolicyEngineConstants.triggerAction()` - runbook execution branch (line 1391)
- Runbook action check: `PolicyTriggerActionType.RUNBOOK` (lines 1394-1410)

**Module:** `com.mindarray.policy.PolicyEngineConstants`
**File:** `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java`

**Control Surface:**
- `EVENT_RUNBOOK` event bus messages (line 1403)
- Runbook context preparation: `prepareContext()` method
- Runbook plugin validation: `RunbookPluginConfigStore.getStore().existItem()` (line 1364)

**Exit Points:**
- Runbook execution via `RunbookEngine` (consumes `EVENT_RUNBOOK` events)
- Runbook execution logs and worklog persistence

**External State:**
- Runbook execution logs
- Worklog persistence (via `RUNBOOK_WORKLOG_*` constants)
- Runbook execution state in `RunbookEngine`

**Event Publication Points:**
1. **Runbook Execution:** `Bootstrap.vertx().eventBus().send(EventBusConstants.EVENT_RUNBOOK, ...)` (line 1403)
   - **IRREVERSIBLE BOUNDARY:** Runbook execution initiation - cannot un-execute runbook actions

**Feature Flag Gates:** None identified

**Permission Checks:** None at this stage (runbook execution permission checked in RunbookEngine)

**Where State Becomes Externally Visible:**
- Runbook execution affects target systems (SSH commands, API calls, etc.)
- Worklog entries visible in UI
- Runbook execution state affects future automation decisions

**Where Rollback Becomes Non-Unilateral:**
- Runbook execution on target systems - requires manual intervention or reverse runbook
- Worklog persistence - historical record cannot be deleted
- Runbook execution state affects future policy evaluation

---

## Module Paths Summary

| Module | File Path | Key Responsibilities |
|--------|-----------|---------------------|
| Policy Management | `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyManager.java` | Policy qualification, query execution, policy assignment |
| Policy Inspection | `motadata/src/main/java/com/mindarray/policy/AIOpsMetricPolicyInspector.java` | Anomaly detection, baseline comparison, forecast evaluation |
| Correlation | `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` | Event correlation, dependency traversal, root cause identification |
| Policy Constants | `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` | Policy flap processing, action triggering, notification dispatch |
| Severity Processor | `motadata/src/main/java/com/mindarray/policy/SeverityChangeEventProcessor.java` | UI notification management, severity change tracking |
| Runbook | `motadata/src/main/java/com/mindarray/runbook/Runbook.java` | Runbook type definitions, compatibility mapping |

## External API Calls

1. **Notification APIs:** Email, SMS, Teams, Slack integration endpoints
2. **Integration APIs:** ServiceNow, Jira, and other ticketing systems (via `EVENT_INTEGRATION`)
3. **Runbook Execution:** SSH, PowerShell, HTTP, SNMP execution endpoints

## Database Write Boundaries

1. **Correlation State:** File persistence (line 443 in AvailabilityCorrelationEngine)
2. **Policy Cache:** `MetricPolicyCacheStore.updateItem()` (line 1017)
3. **Object Status Cache:** `ObjectStatusCacheStore.updateItem()` (lines 273, 813)
4. **Action Event Logs:** `writeTriggeredActionEvent()` calls
5. **Runbook Worklogs:** Worklog persistence via RunbookEngine

## Event Publication Points

1. `EVENT_NOTIFICATION` - External notifications (email/SMS)
2. `EVENT_POLICY_NOTIFICATION` - UI notifications
3. `EVENT_SEVERITY_QUERY` - Real-time UI updates
4. `EVENT_RUNBOOK` - Runbook execution
5. `EVENT_INTEGRATION` - External integration systems
6. `EVENT_CHANGE_NOTIFICATION` - State change notifications
7. Correlation reply topic - Correlation results
