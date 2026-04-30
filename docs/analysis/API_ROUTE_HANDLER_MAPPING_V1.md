# API Route → Handler Mapping (V1)

## Summary

This report captures only wiring proven directly in source. It maps:
- HTTP ingress and route registration in `APIServer.start`
- sub-router composition from `APIServer` to `APIRouter`
- generic CRUD route binding behavior in `AbstractAPI.init`
- confirmed `AbstractAPI` subclasses and lifecycle hook implementations
- event-bus handoff points visible in `APIServer` and `UIActionEventHandler`

No unproven route-to-class or class-to-class call chains are asserted.

## Confirmed route registration points

### APIServer entrypoint

- `APIServer.start(Promise<Void>)` initializes HTTP server and root router.
  - File: `/home/harshil/Projects/Motadata/motadata/src/main/java/com/mindarray/api/APIServer.java`
  - Class: `APIServer`
  - Method: `start`
  - Line range: `331-349`

### Root-level routes in APIServer

Confirmed route registrations include:
- `router.route("/eventbus/*") ... .subRouter(eventBusHandler())` (`408-416`)
- `router.post("/api/v1/token")` (`748+`)
- `router.get("/api/v1/login-metadata")` (`906+`)
- `router.get("/api/v1/sso")` (`921+`)
- `router.post("/api/v1/sso/callback")` (`977+`)
- `router.get("/api/v1/sso/logout")` (`1045+`)
- `router.route("/upload")` (`1175`)
- `router.route("/oauth-callback")` (`1177`)
- `router.route("/upload-firmware")` (`1179`)
- `router.route("/upload-image")` (`1181`)
- `router.route("/download")` (`1183`)
- `router.get("/client-logo")` (`1185`)
- `router.route("/api/v1/*") ... .subRouter(apiRouter)` (`1187`)
- `router.route("/forgot-password")` (`1189`)
- `router.route("/reset-password")` (`1191`)

### APIServer → sub-router binding

Confirmed sub-router namespace bindings:
- `/settings/*` -> `settingsAPIRouter` (`1141`, `1143`)
- `/system/*` -> `systemRouter` (`1145`, `1147`)
- `/audit/*` -> `auditAPIRouter` (`1149`)
- `/user-notification/*` -> `userNotificationAPIRouter` (`1151`)
- `/misc/*` -> `miscRouter` (`1153`, `1155`)
- `/visualization/*` -> `visualizationRouter` (`1157`, `1159`)
- `/query/*` -> `queryRouter` (`1161`)
- `/user/*` -> `userRouter` (`1169`, `1171`)

### APIRouter class registrations

`APIRouter.init(settingsAPIRouter, miscRouter, visualizationRouter, systemRouter, queryRouter)` registers concrete API classes onto those routers (for example: `MailServerConfiguration`, `Discovery`, `MetricPolicy`, `TraceService`, `Query`, etc.).

- File: `/home/harshil/Projects/Motadata/motadata/src/main/java/com/mindarray/api/APIRouter.java`
- Class: `APIRouter`
- Method: `init`
- Line range: `57-231`

## Confirmed API handler classes

### Confirmed base abstraction

- `AbstractAPI` defines generic route binding and lifecycle hooks.
  - File: `/home/harshil/Projects/Motadata/motadata/src/main/java/com/mindarray/api/AbstractAPI.java`
  - Class: `AbstractAPI`
  - Methods: `init(Router)`, `init(Router, Set<String>)`
  - Line range: `91-155`

### Confirmed subclass examples

- `MailServerConfiguration extends AbstractAPI`
  - Constructor endpoint: `"mail-server-configuration"` (`58`)
  - File: `/home/harshil/Projects/Motadata/motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java`
- `User extends AbstractAPI`
  - Constructor endpoint: `"users"` (`145`)
  - File: `/home/harshil/Projects/Motadata/motadata/src/main/java/com/mindarray/api/User.java`
- `TraceService extends AbstractAPI`
  - Constructor endpoint: `"trace-services"` (`76`)
  - File: `/home/harshil/Projects/Motadata/motadata/src/main/java/com/mindarray/api/TraceService.java`

Many additional classes extending `AbstractAPI` are present under the same package and are initialized via `APIRouter.init`.

## AbstractAPI lifecycle map

### Base lifecycle hooks declared

From `AbstractAPI`:
- `beforeDelete(RoutingContext)` (`211`)
- `afterDelete(JsonObject, RoutingContext)` (`216`)
- `beforeUpdate(RoutingContext)` (`231`)
- `afterUpdate(JsonObject, RoutingContext)` (`236`)
- `beforeDeleteAll(RoutingContext)` (`246`)
- `afterDeleteAll(JsonObject, RoutingContext)` (`251`)

### Base CRUD route templates

From `AbstractAPI.init`:
- `POST /{endpoint}/search` -> `search` (`96`)
- `GET /{endpoint}` -> `getAll` (`98`)
- `GET /{endpoint}/:id` -> `validate`, `get` (`100`)
- `POST /{endpoint}` -> `validate`, `create` (`102`)
- `PUT /{endpoint}/:id` -> `validate`, `update` (`104`)
- `DELETE /{endpoint}/:id` -> `validate`, `delete` (`106`)
- `DELETE /{endpoint}` -> `deleteAll` (`108`)

### Confirmed subclass hook implementations (examples)

- `MailServerConfiguration.beforeUpdate` (`63`)
- `MailServerConfiguration.afterUpdate` (`120`)
- `User.beforeUpdate` (`436`)
- `User.beforeDelete` (`543`)
- `TraceService.afterUpdate` (`256`)
- `TraceService.beforeDelete` (`277`)
- `TraceService.afterDelete` (`283`)

## EventBus handoff points

## In APIServer

- Local consumers registered:
  - `EVENT_AUTH_TOKEN_CREATE` (`439`)
  - `EVENT_PAT_CREATE` (`488`)
  - `EVENT_SERVER` (`1223`)
- Event bus sends from request paths:
  - `EVENT_AUDIT` (`817`, `852`, `866`, `876`, `901`, `1013`, `1035`)
  - `EVENT_STREAM_STOP` (`1068`)

## In UIActionEventHandler

- Local consumers registered for UI action addresses (examples):
  - `UI_ACTION_CONFIGURATION_TEST` (`443`)
  - `UI_ACTION_MAIL_SERVER_CONFIGURATION_TEST` (`596`)
  - `UI_ACTION_SMS_GATEWAY_CONFIGURATION_TEST` (`780`)
  - `UI_ACTION_PROXY_SERVER_TEST` (`844`)
  - `UI_ACTION_TWO_FACTOR_AUTHENTICATION_TEST` (`916`)
  - `UI_ACTION_RUNBOOK_PLUGIN_TEST` (`1970`)
- Confirmed handoff pattern:
  - UI action consumer receives event, then sends downstream engine/event addresses such as `EVENT_ADD`, `EVENT_ROUTER`, `EVENT_RUNBOOK` (multiple call sites in the same class).
  - File: `/home/harshil/Projects/Motadata/motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java`

## Unknown / not yet proven links

- Exact `"/api/v1/.../path"` -> specific API class/method mapping is not fully resolved from `APIServer` alone.
- Exact internal `apiRouter` route assembly for each concrete class requires endpoint-by-endpoint extraction from each class constructor + `AbstractAPI.init` calls.
- Exact HTTP route -> event bus address handoff for every API path is not fully proven in this pass.
- Exact `route().handler(...)` sequence for all APIs behind `APIRouter` is partially implied by `AbstractAPI`, but per-class overrides need per-file extraction.

## Recommended next extraction rules for CIG

- Parse `APIRouter.init` registrations as authoritative class registration inventory.
- For each registered class, extract:
  - constructor endpoint string (`super("<endpoint>", ...)`)
  - `init(...)` override behavior (if any)
  - explicit extra route registrations in that class.
- Build deterministic route materialization:
  - `/api/v1` + APIServer namespace (`/settings/*`, `/system/*`, etc.)
  - class endpoint
  - AbstractAPI template method bindings
- Track only direct evidence edges:
  - HTTP route registration edge
  - eventBus send/request/publish edge
  - eventBus consumer edge
  - inheritance edge (`extends AbstractAPI` / `extends AbstractVerticle`)
