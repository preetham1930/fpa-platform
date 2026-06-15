# 0001: Phase 1 Architecture

## Context
We are building Phase 1 of the FP&A Platform, a local-only vertical slice showing budget-vs-actual variance.
We need to establish the initial stack and patterns.

## Decisions

1. **Stack**: FastAPI + SQLAlchemy + Pydantic for backend. React + Vite + Recharts for frontend. Postgres for the database.
2. **Database Migrations**: For Phase 1, we will use SQLAlchemy's `metadata.create_all()` locally since the local DB is considered throwaway. We will introduce `Alembic` for migrations when we deploy to Cloud SQL and data needs to persist safely across schema changes.
3. **Period Modeling**: The `Period` model uses a string `name` (e.g., "2024-01") for display and ease of use, but also includes `start_date` and `end_date` fields for robust querying.
4. **Variance Spec**: 
   - `variance = actual - budget`
   - Revenue: over-budget is favorable.
   - Cost: over-budget is unfavorable.
   - We return None for percentage variance if budget is 0, and treat actual == budget (variance 0) as favorable/neutral explicitly.

## Consequences
- Fast initial velocity.
- Will require migration scripts setup later when moving to cloud.
