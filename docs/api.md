# API

The REST API is exposed under `/api/v1`. OpenAPI is available at `/docs`.

## Missions

Create an assigned mission on an existing graph map:

```http
POST /api/v1/missions
GET /api/v1/missions/{mission_id}
Content-Type: application/json

{
  "mapId": "<map-id>",
  "assignedRobotId": "<robot-id>",
  "startNodeKey": "Dock",
  "goalNodeKey": "Shelf",
  "priority": 0
}
```

Both nodes must exist on the selected map. A mission created with a robot starts as
`assigned`; without a robot it starts as `queued`.

Dispatch an assigned mission:

```http
POST /api/v1/missions/{mission_id}/dispatch
```

Dispatch calculates the weighted shortest path, builds and validates a VDA 5050 order,
publishes it to the robot's `order` topic, stores the payload in `mission_orders`, and moves
the mission to `sent`. The outbound `headerId` is incremented per robot order stream.

## MQTT/VDA message logs

```http
GET /api/v1/mqtt/messages
```

Supported query parameters:

- `direction`: `inbound` or `outbound`.
- `messageType`: VDA message type such as `state`, `connection`, or `order`.
- `robotId`: internal robot identifier.
- `schemaValid`: `true` or `false`.
- `page`: one-based page number; defaults to `1`.
- `pageSize`: between `1` and `100`; defaults to `50`.

Results are ordered newest first and include the original JSON payload, validation errors, QoS,
retain flag, total result count, and page count.

## Real-time events

```text
WS /api/v1/events/ws
```

Each message has a stable envelope:

```json
{
  "id": "<event-id>",
  "type": "robot.state.updated",
  "timestamp": "2026-06-29T20:00:00.000Z",
  "robotId": "<robot-id>",
  "payload": {}
}
```

Implemented event types:

- `robot.discovered`, `robot.connection.updated`, `robot.factsheet.updated`,
  `robot.state.updated`;
- `mission.created`, `mission.assigned`, `mission.dispatched`,
  `mission.status.changed`;
- `mqtt.message.received`, `mqtt.message.published`, `vda.validation.failed`.

The event bus is process-local for the MVP. Each connection has a bounded buffer; if a client
cannot keep up, its oldest pending event is discarded without blocking robot or MQTT processing.

## Robot instant actions

```http
POST /api/v1/robots/{robot_id}/instant-actions
Content-Type: application/json

{
  "actionType": "cancelOrder"
}
```

The backend assigns an action ID and a monotonic `headerId` for the robot's `instantActions`
stream, validates the VDA 5050 payload, publishes it with QoS 0, and persists the outbound log.

## Graph maps

```text
GET  /api/v1/maps
POST /api/v1/maps
GET  /api/v1/maps/{map_id}
POST /api/v1/maps/{map_id}/nodes
PATCH /api/v1/maps/{map_id}/nodes/{node_key}
POST /api/v1/maps/{map_id}/edges
POST /api/v1/maps/{map_id}/route-preview
PUT  /api/v1/maps/{map_id}/background
GET  /api/v1/maps/{map_id}/background/content
PUT  /api/v1/maps/{map_id}/background/calibration
DELETE /api/v1/maps/{map_id}/background
POST /api/v1/maps/{map_id}/obstacles
DELETE /api/v1/maps/{map_id}/obstacles/{obstacle_id}
```

Background upload accepts raw PNG/JPEG bytes and a `filename` query parameter. Calibration accepts
two pixel points and their corresponding metric world points. Map details return the derived
meters-per-pixel, image origin, and rotation used by the frontend overlay.

Obstacle polygons use metric map coordinates. Route planning excludes an edge when its segment,
buffered by the configured robot radius and the obstacle safety margin, intersects that polygon.

Map detail returns the complete node and edge graph used by the operator editor. Nodes carry
Cartesian position and orientation; edges carry direction, distance, and bidirectional metadata.
Bulk import/export and external map-format adapters are post-v1 roadmap items.
