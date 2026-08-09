# Sprint 11 Report — Planning Board and Loading Optimization

Date: 2026-08-09

## Summary

Sprint 11 delivers the dispatcher planning board, assignment visibility, trailer loading visualization, and AI-assisted loading optimization with mandatory human approval.

## Planning architecture

```text
Dispatcher UI (Planning Board / Loading Board)
        │
        ▼
PlanningService
   ├── RoutePlanner
   ├── LoadingOptimizer
   └── CapacityValidator
        │
        ▼
 loading_plans + loading_positions
        │
        ▼
 AI suggestions (LOADING_OPTIMIZATION) → approve → persist
```

Business assignment still flows through `OrderService.assign_driver`. Loading plans never auto-apply.

## Loading optimization

| Component | Responsibility |
|-----------|----------------|
| `LoadingOptimizer` | Deck-aware slot assignment, loading/unloading sequence, height/weight estimates |
| `CapacityValidator` | Count, height, weight, axle balance, duplicates, unloading feasibility |
| `RoutePlanner` | Pickup-then-delivery stop order, travel distance heuristic |

Model version: `prodrive-heuristic-loading-1.0`

## Validation rules

Prevented conditions:

* Duplicate trailer positions or vehicles
* Over-capacity vehicle count
* Height above trailer/legal limit
* Weight above trailer maximum
* Skewed axle distribution (warning)
* Impossible unloading sequences
* Incompatible trailer hints (warning)

## UI components

| Component | Purpose |
|-----------|---------|
| `PlanningBoardPage` | Kanban columns, filters, drag-and-drop assignment |
| `AssignmentBoard` | Driver/truck/trailer availability and conflicts |
| `LoadingBoardPage` | Per-order loading editor |
| `TrailerVisualization` | Upper/lower deck slot editor |
| `OptimizationPanel` | AI recommendation with approve/reject |
| `ValidationPanel` | Capacity validation feedback |

Routes: `/planning`, `/planning/loading/:orderId`

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/planning/board` | Planning kanban + resources |
| POST | `/planning/assign` | Assign/reassign/clear |
| POST | `/planning/load-plan` | Save draft or confirm plan |
| GET | `/planning/load-plan/{order_id}` | Fetch latest plan |
| POST | `/planning/optimize` | AI loading suggestion |
| POST | `/planning/validate` | Validate draft positions |

## Test results

| Area | Tests |
|------|-------|
| Loading optimizer | `backend/app/planning/tests/test_loading_optimizer.py` |
| Integration | `backend/tests/test_planning_sprint11.py` |

Run:

```bash
cd backend && pytest tests/test_planning_sprint11.py app/planning/tests/ -q
```

## Known limitations

* Travel distance uses deterministic city-pair heuristics (no GPS routing)
* Drag-and-drop assignment requires driver filter selection for assign column drops
* Single loading plan per order (latest wins)
* `EXPIRED` suggestion status not scheduled
* Vehicle length/width not modeled — height/weight only

## Recommendations for Sprint 12

1. Integrate external LLM for complex loading edge cases (feature-flagged)
2. Real routing/travel-time provider for route planner
3. Persist multiple loading plan revisions with diff view
4. Fleet assignment CRUD in planning UI
5. Push notifications when optimization awaits approval
6. Driver app loading plan read-only view

## Definition of Done

- [x] Planning Board works
- [x] Assignments work
- [x] Trailer visualization works
- [x] Loading optimization works
- [x] Capacity validation works
- [x] Height calculation works
- [x] Route sequencing works
- [x] AI recommendations require approval
- [x] Tests implemented
- [x] Documentation updated
