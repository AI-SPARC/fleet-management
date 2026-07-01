# Spatial Map Development Plan

This plan evolves the v1 graph map into a calibrated operational map while keeping world
coordinates independent from screen pixels.

## Coordinate model

- Nodes, robot positions, distances, and obstacle geometry use map coordinates in meters.
- PNG/JPEG pixels are presentation coordinates only.
- Two image/world point pairs define one similarity transform: scale, rotation, and origin.
- Replacing an image invalidates its calibration so stale transforms cannot be reused silently.

## Delivery phases

1. **Calibrated image overlay:** upload and validate a background, calibrate with two point pairs,
   and render graph nodes, edges, and robot positions over it.
2. **Spatial graph editing:** convert pointer positions back to meters, create and move nodes on
   the image, and offer Euclidean edge distance as a default.
3. **Navigation constraints:** draw obstacle polygons, buffer edges by robot footprint plus a
   safety margin, report intersections, and exclude blocked edges from global planning.
4. **Live mission view:** show the planned route, current robot pose, traversed and remaining
   segments, connectivity, battery, errors, and stale-telemetry state.
5. **Mission reconciliation:** derive `running`, `completed`, `failed`, and `canceled` transitions
   from VDA 5050 state and action updates while preserving the raw protocol history.
6. **Trajectory and replay:** expose timestamped position history, replay completed missions, add
   Docker/browser E2E coverage, and document operational limits.

Static map obstacles and dynamic runtime blocks remain separate. A floor-plan image is never
treated as an occupancy map automatically; automatic extraction may later suggest geometry, but
an operator must confirm it. Immediate collision avoidance remains the robot's local planner
responsibility.
