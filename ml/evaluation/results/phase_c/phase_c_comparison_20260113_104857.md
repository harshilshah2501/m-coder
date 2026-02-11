# Phase-C: CPT Completion Probe - Detailed Comparison

**Timestamp:** 20260113_104857

**Verdict:** ⚠️  PHASE-C MARGINAL

**CPT Win Rate:** 60.0%

---

## probe_01: EventRouter.route

**Category:** Class/Method

**Winner:** CPT

### Prompt
```java
public class EventRouter {

    private final EventBus eventBus;

    public EventRouter(EventBus eventBus) {
        this.eventBus = eventBus;
    }

    public void route(Event event) {
        // COMPLETE

```

### BASE Completion
```java
// 1. Get the event type from the event
        // 2. Get the event handler from the event bus
        // 3. If the event handler is not null, call the handle method on the event handler
        // 4. If the event handler is null, throw a RuntimeException with the message "No handler for event type: " + eventType
        // 5. If the event handler is not null, call the handle method on the event handler
        // 6. If the event handler is null, throw a RuntimeException with the message "No handler for event type: " + eventType
        // 7. If the event handler is not null, call the handle method on the event handler
```
**Score:** 1/5 (Domain: 0, Structure: 1, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

### CPT Completion
```java
// 1. Determine the event type (e.g., "metric", "log", "trace", "policy")
        // 2. Based on the event type, publish to the appropriate event bus topic
        // 3. For policy events, also publish to the policy engine topic
        // 4. Handle any special routing requirements (e.g., high priority events)
    }
}
```

### 4. **Event Processor**

- **Purpose**: Processes events based on their type and content.
- **Responsibilities**:
  - Deserializes event data.
  - Validates event content.
  - Routes events to appropriate handlers.
  - Handles event-specific logic (e.g., aggregation, filtering).

```java
```
**Score:** 2/5 (Domain: 0, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

---

## probe_02: AbstractAPI Extension

**Category:** Class/Method

**Winner:** CPT

### Prompt
```java
public class DiscoveryAPI extends AbstractAPI {
    
    @Override
    public void initialize() {
        // COMPLETE

```

### BASE Completion
```java
}
    
    @Override
    public void start() {
        // COMPLETE
    }
    
    @Override
    public void stop() {
        // COMPLETE
    }
    
    @Override
    public void destroy() {
        // COMPLETE
    }
    
    @Override
    public void handleRequest(Request request) {
        // COMPLETE
    }
    
    @Override
    public void handleResponse(Response response) {
        // COMPLETE
    }
    
    @Override
    public void handleError(Error error) {
        // COMPLETE
    }
    
    @Override
    public void handleEvent(Event event) {
        // COMPLETE
    }
    
    @Override
    public void handleNotification(Notification notification) {
        // COMPLETE
```
**Score:** 2/5 (Domain: 0, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

### CPT Completion
```java
}
    
    @Override
    public void get(Request request) {
        try {
            if (request.parameters.containsKey(REQUEST_TYPE)) {
                if (REQUEST_TYPE_TOGETHER.equalsIgnoreCase(request.parameters.get(REQUEST_TYPE))) {
                    var items = new JsonArray();
                    
                    var objectItems = ObjectConfigStore.getStore().getItemsByUserProfile(request.user.getLong(ID));
                    
                    var pluginItems = PluginEngineCacheStore.getStore().getItemsByUserProfile(request.user.getLong(ID));
                    
                    for (var index = 0; index < objectItems.size(); index++) {
                        var item = objectItems.getJsonObject(index);
                        
                        if (pluginItems.contains(item.getString(AIOpsObject.OBJECT_PLUGIN))) {
                            items.add(item);
```
**Score:** 3/5 (Domain: 1, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** ConfigStore

---

## probe_03: ConfigStore Getter

**Category:** Class/Method

**Winner:** BASE

### Prompt
```java
public class ServiceConfig extends AbstractConfigStore {
    
    public String getServiceUrl() {
        // COMPLETE

```

### BASE Completion
```java
return null;
    }
    
    public String getServiceName() {
        // COMPLETE
        return null;
    }
    
    public String getServiceVersion() {
        // COMPLETE
        return null;
    }
    
    public String getServiceDescription() {
        // COMPLETE
        return null;
    }
    
    public String getServiceContact() {
        // COMPLETE
        return null;
    }
    
    public String getServiceContactEmail() {
        // COMPLETE
        return null;
    }
    
    public String getServiceContactPhone() {
        // COMPLETE
        return null;
    }
    
    public String getServiceContactAddress() {
        // COMPLETE
        return null;
    }
    
    public String getServiceContactCity() {
        // COMPLETE
        return
```
**Score:** 2/5 (Domain: 0, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

### CPT Completion
```java
}
    
    public int getServicePort() {
        // COMPLETE
    }
    
    public String getServiceProtocol() {
        // COMPLETE
    }
    
    public String getServiceType() {
        // COMPLETE
    }
    
    public String getServiceVersion() {
        // COMPLETE
    }
    
    public String getServiceEnvironment() {
        // COMPLETE
    }
    
    public String getServiceStatus() {
        // COMPLETE
    }
    
    public String getServiceHealth() {
        // COMPLETE
    }
    
    public String getServiceDeploymentType() {
        // COMPLETE
    }
    
    public String getServiceDeploymentLocation() {
        // COMPLETE
    }
    
    public String getServiceDeploymentMethod() {
        // COMPLETE
    }
    
    public String getService
```
**Score:** 0/5 (Domain: 0, Structure: 2, Brevity: 0, Hallucinations: -2)

**Motadata tokens:** none

---

## probe_04: Bootstrap Startup

**Category:** Registration/Wiring

**Winner:** CPT

### Prompt
```java
public class BootstrapSecondary {
    
    public void start() {
        // COMPLETE

```

### BASE Completion
```java
// Create a new instance of the Secondary class
        // Call the start method on the Secondary class
        // You can use the following code to create a new instance of the Secondary class:
        // Secondary secondary = new Secondary();
        // You can use the following code to call the start method on the Secondary class:
        // secondary.start();
        // You can use the following code to create a new instance of the Secondary class and call the start method on it:
        // new Secondary().start();
        // You can use the following code to create a new instance of the Secondary class and call the start method on it:
        // new Secondary().start();
        // You can use the following code to create a new instance of the
```
**Score:** 2/5 (Domain: 0, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

### CPT Completion
```java
}
}<|fim_middle|>
        "application.mapper.protocol": "TCP",
```
**Score:** 3/5 (Domain: 0, Structure: 2, Brevity: 1, Hallucinations: 0)

**Motadata tokens:** none

---

## probe_05: APIRouter Registration

**Category:** Registration/Wiring

**Winner:** BASE

### Prompt
```java
public void registerAPIs(APIRouter router) {
    // COMPLETE

```

### BASE Completion
```java
router.registerAPI("GET", "/api/teams", (request, response) -> {
        return new JSONObject().put("teams", Team.getTeams());
    });
    router.registerAPI("GET", "/api/teams/:id", (request, response) -> {
        return Team.getTeam(request.params(":id"));
    });
    router.registerAPI("POST", "/api/teams", (request, response) -> {
        return Team.createTeam(request.body());
    });
    router.registerAPI("PUT", "/api/teams/:id", (request, response) -> {
        return Team.updateTeam(request.params(":id"), request.body());
    });
    router.registerAPI("DELETE", "/api/teams/:id", (request, response
```
**Score:** 4/5 (Domain: 2, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** router.register, API

### CPT Completion
```java
router.get("/v1/complete", CompleteRequestHandler.class, new JsonObject().put(REQUEST_TRANSFER, true));

    // CONFIG
    router.get("/v1/config", ConfigRequestHandler.class, new JsonObject().put(REQUEST_TRANSFER, true));

    // EVENT
    router.post("/v1/event", EventRequestHandler.class, new JsonObject().put(REQUEST_TRANSFER, true));

    // EVENT SOURCE
    router.get("/v1/event-source", EventSourceRequestHandler.class, new JsonObject().put(REQUEST_TRANSFER, true));

    // EVENT SOURCE
    router.get("/v1/event-source/:id", EventSourceRequestHandler.class, new JsonObject().put(REQUEST_TRANSFER, true));

    // EVENT SOURCE
    router.get("/v
```
**Score:** 2/5 (Domain: 0, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

---

## probe_06: LocalEventChangeNotificationHandler

**Category:** Handler/Processor

**Winner:** CPT

### Prompt
```java
public class LocalEventChangeNotificationHandler {
    
    @Override
    public void handle(Event event) {
        // COMPLETE

```

### BASE Completion
```java
// 1. Get the event type
        // 2. Get the event data
        // 3. Get the event source
        // 4. Get the event timestamp
        // 5. Get the event id
        // 6. Get the event version
        // 7. Get the event correlation id
        // 8. Get the event causation id
        // 9. Get the event causation version
        // 10. Get the event causation correlation id
        // 11. Get the event causation causation id
        // 12. Get the event causation causation version
        // 13. Get the event causation
```
**Score:** 1/5 (Domain: 0, Structure: 1, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

### CPT Completion
```java
}
}<|fim_middle|>
import com.vmops.api.SLOConstants;
import com.vmops.api.UserConstants;
import com.vmops.eventbus.EventBusConstants;
import com.vmops.model.*;
import com.vmops.store.*;
import com.vmops.util.*;
import io.vertx.core.AbstractVerticle;
import io.vertx.core.Promise;
import io.vertx.core.json.JsonArray;
import io.vertx.core.json.JsonObject;

import java.util.*;
import java.util.stream.Collectors;

import static com.vmops.api.APIConstants.*;
import static com.vmops.api.UserConstants.USER_PREFERENCE;
import static com.vmops.eventbus.EventBusConstants.*;
import static com.vmops.util.CommonUtil.*;
import static com.vmops.util.LoggerUtil.*;

/**
 * The LocalEventChangeNotificationHandler class is
```
**Score:** 4/5 (Domain: 2, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** JsonObject, EventBusConstants, notification

---

## probe_07: Event Processing

**Category:** Handler/Processor

**Winner:** TIE

### Prompt
```java
private void processEvent(JsonObject event) {
    String type = event.getString(EVENT_TYPE);
    // COMPLETE

```

### BASE Completion
```java
if (type.equals(EVENT_TYPE_COMPLETE)) {
String id = event.getString(EVENT_ID);
if (id != null) {
    Future<JsonObject> future = futures.remove(id);
    if (future != null) {
future.complete(event);
    }
}
    } else if (type.equals(EVENT_TYPE_ERROR)) {
String id = event.getString(EVENT_ID);
if (id != null) {
    Future<JsonObject> future = futures.remove(id);
    if (future != null) {
future.fail(event.getString(EVENT_ERROR));
    }
}
    } else if (type.equals(EVENT_TYPE_MESSAGE)) {
String id = event.getString(EVENT_ID);
if (id != null) {
    Future<JsonObject> future = futures.remove(id);
    if (future !=
```
**Score:** 2/5 (Domain: 0, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

### CPT Completion
```java
if (type.equalsIgnoreCase(EVENT_TYPE_METRIC_POLL) || type.equalsIgnoreCase(EVENT_TYPE_TOPOLOGY_MAP_POLL) || type.equalsIgnoreCase(EVENT_TYPE_DISCOVERY) || type.equalsIgnoreCase(EVENT_TYPE_LOG_TAIL) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_STATS) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_DISABLE) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_ENABLE) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_DELETE) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_UPGRADE) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_INSTALL) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_CONFIG_UPDATE) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_FILE_TRANSFER) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_FILE_DELETE) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_FILE_DOWNLOAD) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_FILE_UPLOAD) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_FILE_READ) || type.equalsIgnoreCase(EVENT_TYPE_AGENT_FILE_WRITE
```
**Score:** 2/5 (Domain: 0, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

---

## probe_08: Message Handler

**Category:** Handler/Processor

**Winner:** CPT

### Prompt
```java
eventBus.consumer(EventBusConstants.EVENT_NOTIFICATION, message -> {
    JsonObject body = message.body();
    // COMPLETE

```

### BASE Completion
```java
// 1. Get the notification type from the body
    // 2. Get the notification message from the body
    // 3. Get the notification timestamp from the body
    // 4. Get the notification user from the body
    // 5. Get the notification user id from the body
    // 6. Get the notification user name from the body
    // 7. Get the notification user email from the body
    // 8. Get the notification user phone from the body
    // 9. Get the notification user address from the body
    // 10. Get the notification user city from the body
    // 11. Get the notification user state from the
```
**Score:** 1/5 (Domain: 0, Structure: 1, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** none

### CPT Completion
```java
if (body.getString(RESULT).equalsIgnoreCase(EMPTY_VALUE))
    {
        LOGGER.info(String.format("notification failed to send to %s with reason %s", message.body().getString(Notification.NotificationType.EMAIL.getName()), message.body().getString(ERROR)));
    }
    else
    {
        LOGGER.info(String.format("notification successfully sent to %s", message.body().getString(Notification.NotificationType.EMAIL.getName())));
    }
});

eventEngine = new EventEngine().setEventType(config().getString(EVENT_TYPE))
        .setPersistEventOffset(true)
        .setEventQueueSize(1)
        .setEventHandler(this::send)
        .setLogger(LOGGER)
        .start(vertx, promise);
}<|fim_middle|>            }
```
**Score:** 4/5 (Domain: 2, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** body.get, getString, handle

---

## probe_09: Vertx Execute Blocking

**Category:** Async/Vertx

**Winner:** BASE

### Prompt
```java
vertx.executeBlocking(promise -> {
    // COMPLETE

```

### BASE Completion
```java
promise.complete("Hello World");
}, res -> {
    // RESULT
    System.out.println("The result is: " + res.result());
});
```
**Score:** 5/5 (Domain: 2, Structure: 2, Brevity: 1, Hallucinations: 0)

**Motadata tokens:** promise.complete, result

### CPT Completion
```java
promise.complete();
}, false, result -> {
    // COMPLETE
});
```

In the first example, the `executeBlocking` method is called with a lambda expression that contains the code to be executed in a separate thread. The second parameter `false` indicates that the method should not be executed on the event loop thread. The third parameter is a handler that will be called when the blocking operation is complete.

In the second example, the `executeBlocking` method is called with a lambda expression that contains the code to be executed in a separate thread. The second parameter `false` indicates that the method should not be executed on the event loop thread. The third parameter is a handler that will be called when the blocking operation is complete.

By
```
**Score:** 4/5 (Domain: 2, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** promise.complete, result

---

## probe_10: EventBus Async Publish

**Category:** Async/Vertx

**Winner:** CPT

### Prompt
```java
public void notifyChange(String entityId) {
    Event event = new EntityChangeEvent(entityId);
    // COMPLETE

```

### BASE Completion
```java
for (Observer observer : observers) {
observer.update(event);
    }
}
```
**Score:** 3/5 (Domain: 0, Structure: 2, Brevity: 1, Hallucinations: 0)

**Motadata tokens:** none

### CPT Completion
```java
event.put(ENTITY_PROPERTY, new JsonObject().put(ENTITY_TYPE, config().getString(ENTITY_TYPE)).put(ENTITY_ID, entityId).put(CHANGE_NOTIFICATION_TYPE, ChangeNotificationType.UPDATE.name()).put(CHANGE_NOTIFICATION_ACTION, ChangeNotificationAction.NOTIFY.name()).put(CHANGE_NOTIFICATION_TIMESTAMP, DateTimeUtil.currentSeconds()).put(CHANGE_NOTIFICATION_WORKER_UUID, config().getString(CHANGE_NOTIFICATION_WORKER_UUID)));

    vertx.eventBus().send(EVENT_CHANGE_LOCAL_NOTIFICATION, event);
}
```
**Score:** 4/5 (Domain: 2, Structure: 2, Brevity: 0, Hallucinations: 0)

**Motadata tokens:** JsonObject, vertx

---

