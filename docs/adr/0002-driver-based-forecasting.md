# 0002: Driver-Based Forecasting

**Status:** Accepted

## Context
Phase 1 stored static budgets. To support Anaplan-style planning we needed forecasts driven by editable assumptions, plus what-if scenarios.

## Decisions

1. **Driver Values:** A `Driver` represents a named assumption. `DriverValue` is a join table (driver, scenario) carrying the value, ensuring each scenario holds its own independent set of driver values (many-to-many with a payload)—this is what makes scenarios possible.
2. **Forecast Rules:** `ForecastRule` links an account to a set of drivers. The forecast is computed as the PRODUCT of those drivers' values (a structured model).
3. **Structured Product Model:** We chose the structured product model over storing formula strings to strictly avoid an eval/expression-injection surface; richer formulas remain a future option.
4. **Variance Reusability:** `forecast-vs-budget` reuses the Phase 1 variance engine (same favorable/unfavorable calc) acting as a single source of truth.
5. **Database Migrations:** Kept `create_all` for the additive schema; Alembic is still deferred.

## Consequences
- Scenarios are first-class and the what-if is live.
- No duplicated favorability logic across the application.
- Safe execution environment (no eval).

**Trade-offs:**
- Rules are strictly product-only (sums happen at aggregation, not within a single rule).
- Alembic implementation remains deferred.
- Single period (2026-05) in the UI for now.
