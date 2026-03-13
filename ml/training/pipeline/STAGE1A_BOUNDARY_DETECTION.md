# Phase 1A: Irreversible Boundary Detection Heuristic

## Boundary Classification Table

| Boundary Location | Boundary Type | Classification | Rollback Dependency | Heuristic Rule Applied |
|-------------------|---------------|----------------|---------------------|----------------------|
| `PolicyEngineConstants.triggerAction()` → `EVENT_NOTIFICATION` (Email, line 1259) | Alert Publication | Contract Exposure | External email systems (SMTP servers) | Rule 1: Publishes alert externally (UI/API visible) |
| `PolicyEngineConstants.triggerAction()` → `EVENT_NOTIFICATION` (SMS, line 1288) | Alert Publication | Contract Exposure | External SMS gateways | Rule 1: Publishes alert externally (UI/API visible) |
| `PolicyEngineConstants.triggerAction()` → `Notification.send()` (Teams/Slack, line 1375) | Alert Publication | Contract Exposure | Microsoft Teams/Slack APIs | Rule 1: Publishes alert externally (UI/API visible) |
| `PolicyEngineConstants.triggerAction()` → `EVENT_RUNBOOK` (line 1403) | Automation Execution | Automation Execution | Runbook execution state, worklog persistence, target system state | Rule 3: Enables or triggers automation execution |
| `AvailabilityCorrelationEngine` → File persistence (line 443) | Correlation Graph Write | Organizational Commitment | Correlation state affects future anomaly scoring and root cause analysis | Rule 2: Writes to persistent datastore affecting correlation graph |
| `MetricPolicyCacheStore.updateItem()` (line 1017) | Policy State Persistence | Contract Exposure | UI alert visibility, severity counts, alert widget state | Rule 1: Publishes alert externally (UI/API visible) |
| `PolicyEngineConstants.processPolicyFlap()` → `EVENT_POLICY_NOTIFICATION` (SeverityChangeEventProcessor line 258) | UI Alert Publication | Contract Exposure | Real-time UI state, user notification popups, alert counts | Rule 1: Publishes alert externally (UI/API visible) |
| Correlation → `ObjectStatusCacheStore.updateItem()` (line 273, 813) | Object Status Update | Contract Exposure | UI object status display, topology visualization | Rule 1: Publishes alert externally (UI/API visible) |
| Correlation → `enableMetric()` / `suspendMetric()` calls (via event bus) | Metric State Change | Automation Execution | Affects future data collection and policy evaluation | Rule 4: Updates baseline parameters affecting future anomaly scoring |
| `PolicyEngineConstants.triggerAction()` → `EVENT_INTEGRATION` (line 1425) | Integration Event | Contract Exposure | External ticketing/monitoring systems (ServiceNow, Jira, etc.) | Rule 7: Emits events to downstream systems |
| `writeTriggeredActionEvent()` calls | Action Event Logging | Organizational Commitment | Historical audit trail, compliance reporting | Rule 2: Writes to persistent datastore affecting correlation graph |

## Boundary Inference Rules Applied

### Rule 1: Publishes an alert externally (UI/API visible)
**Applied to:**
- Email notifications (line 1259, 1478)
- SMS notifications (line 1288, 1504)
- Teams/Slack notifications (line 1375, 1560)
- UI notifications via `EVENT_POLICY_NOTIFICATION` (SeverityChangeEventProcessor line 258)
- Object status cache updates (line 273, 813)
- Policy cache updates (line 1017)

**Rationale:** Once an alert is published to external systems (email, SMS, Teams, Slack) or made visible in the UI, it cannot be un-sent or un-displayed without coordination with those external systems or user interaction.

### Rule 2: Writes to persistent datastore affecting correlation graph
**Applied to:**
- Correlation file persistence (line 443)
- Action event logging (`writeTriggeredActionEvent()`)

**Rationale:** Correlation state persistence affects future root cause analysis and anomaly scoring. Historical event logs affect compliance and audit trails. Rollback requires file system access and coordination.

### Rule 3: Enables or triggers automation execution
**Applied to:**
- Runbook execution initiation (line 1403)
- Metric state changes (`enableMetric()` / `suspendMetric()`)

**Rationale:** Runbook execution performs actions on target systems (SSH commands, API calls, etc.) that cannot be automatically reversed. Metric state changes affect future data collection pipeline.

### Rule 4: Updates baseline parameters affecting future anomaly scoring
**Applied to:**
- Metric state changes (`enableMetric()` / `suspendMetric()`)
- Policy cache updates (line 1017)

**Rationale:** Changes to metric collection state affect future baseline calculations and anomaly detection accuracy. Policy state updates affect future policy evaluation decisions.

### Rule 7: Emits events to downstream systems
**Applied to:**
- Integration events (`EVENT_INTEGRATION`, line 1425)

**Rationale:** Events sent to external ticketing/monitoring systems (ServiceNow, Jira, etc.) require API coordination to rollback and may trigger external workflows.

## Boundary Classification Details

### Contract Exposure Boundaries
**Definition:** Actions that expose system state or decisions to external parties (users, external systems, APIs) where rollback requires coordination with those external parties.

**Boundaries:**
1. Email/SMS/Teams/Slack notifications
2. UI alert visibility
3. Integration system events
4. Object status cache updates

**Rollback Dependency:** Requires coordination with external notification systems, user interaction, or API calls to external systems.

### Automation Execution Boundaries
**Definition:** Actions that trigger automated remediation or system changes that cannot be automatically reversed.

**Boundaries:**
1. Runbook execution initiation
2. Metric state changes (enable/suspend)

**Rollback Dependency:** Requires manual intervention, reverse runbooks, or event bus coordination to restore previous state.

### Organizational Commitment Boundaries
**Definition:** Actions that commit organizational state to persistent storage affecting future decision-making or compliance.

**Boundaries:**
1. Correlation graph persistence
2. Action event logging

**Rollback Dependency:** Requires file system access, database coordination, and may affect compliance/audit requirements.

## Boundary Stability Analysis

### High-Stability Boundaries (Clear Irreversibility)
1. **Email/SMS/Teams/Slack notifications** - Cannot un-send messages
2. **Runbook execution** - Cannot un-execute commands on target systems
3. **Correlation file persistence** - Persistent state affects future analysis

### Medium-Stability Boundaries (Coordination Required)
1. **UI notifications** - Requires user interaction to clear
2. **Integration events** - Requires API coordination to rollback
3. **Policy cache updates** - Requires cache store coordination

### Low-Stability Boundaries (Potentially Reversible)
1. **Metric state changes** - Can be reversed via event bus messages
2. **Object status cache** - Can be updated via cache store operations

## Stress Surfaces

**Conditions that test boundary stability:**

1. **Network failures during notification dispatch** - Partial notification delivery
2. **Runbook execution failures** - Partial command execution
3. **File system failures during correlation persistence** - Corrupted correlation state
4. **Cache store failures** - Inconsistent policy state
5. **Event bus failures** - Lost state change events
6. **External API failures** - Failed integration events

## Boundary Validation

**Validation Criteria:**
- ✓ Boundary exists only where rollback ceases to be unilateral
- ✓ All boundaries classified according to heuristic rules
- ✓ No boundary assumed at "risk detection" - boundaries exist at actual state change points
- ✓ Each boundary has explicit rollback dependency identified
