# FP&A Variance Platform

> An internal financial planning & analysis tool that computes budget-vs-actual variance with correct favorable/unfavorable logic for revenue vs cost accounts.

**Live demo:** https://fpa-frontend-1029461300479.asia-south1.run.app

![Dashboard](docs/screenshot.png)

## Overview

The FP&A Variance Platform represents the kind of robust, internal financial tooling typically built by corporate engineering teams to track departmental performance. It solves the critical business need of separating revenue and cost accounts to compute accurate variance logic, ensuring stakeholders can reliably identify positive and negative discrepancies. The application is deployed full-stack on Google Cloud.

## Architecture

```mermaid
flowchart LR
    Client([Web Browser]) --> Frontend[React/Vite<br>Cloud Run via Nginx]
    Frontend --> Backend[FastAPI<br>Cloud Run]
    Backend --> DB[(Cloud SQL<br>PostgreSQL)]
    Backend -.-> Secrets[Secret Manager]
```

The system leverages a decoupled architecture. The React single-page application is served via an Nginx container on Google Cloud Run. It communicates with a stateless Python FastAPI backend, which relies on Google Secret Manager for secure credential injection and connects directly to a managed Cloud SQL Postgres instance via a secure Unix socket.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Pydantic, PostgreSQL
- **Frontend:** React, Vite, TypeScript, Recharts
- **Infrastructure:** Google Cloud Run, Cloud SQL, Secret Manager, Cloud Build
- **Tooling:** Docker, pytest

## Key Features

- **Context-Aware Variance Logic:** Computes budget-vs-actual variance with an intelligent favorable/unfavorable sign-flip based on account type (revenue over budget = favorable; cost over budget = unfavorable).
- **Separated KPIs:** High-level key performance indicator summaries that track total revenue and total cost independently.
- **Premium Visualization:** A detailed variance dashboard featuring an interactive chart and a comprehensive table, styled with a warm, "fintech" aesthetic design system.

## Running Locally

1. **Database:** Spin up the local Postgres instance.
   ```bash
   docker-compose up -d
   ```
2. **Backend:** Initialize the Python environment, run the database seed script, and start the API from the repository root.
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   pip install -r backend/requirements.txt
   
   # Set PYTHONPATH so the backend module resolves correctly
   export PYTHONPATH=.
   # On Windows PowerShell: $env:PYTHONPATH = "."
   
   python backend/seed.py
   uvicorn backend.main:app --reload
   ```
3. **Frontend:** Install dependencies and run the development server.
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Deployment

The platform is fully containerized and deployed to Google Cloud Run, backed by a Cloud SQL PostgreSQL instance. For a detailed breakdown of the infrastructure pipeline—including specific challenges encountered during deployment and their respective solutions—please refer to the [Deployment Log](docs/deployment.md).

## Engineering Decisions

Key architectural choices are documented in the [ADR Directory](docs/adr/). Two foundational decisions include:
- **Migrations:** Utilizing SQLAlchemy's `create_all` for rapid prototyping in Phase 1, with the explicit intent to migrate to Alembic once the data model matures and persistent schema evolution becomes necessary.
- **Environment-Driven Connectivity:** Designing the database connection layer to dynamically switch between standard TCP routing for local development and secure Unix sockets when running in the cloud.

## Roadmap

- **Phase 1:** Core application and cloud deployment (Complete).
- **Phase 2:** Driver-based forecasting and advanced scenario modeling.
- **Phase 3:** ERP/SAP integration layer for automated synchronization.
- **Phase 4:** High-throughput data pipeline (Pub/Sub -> Dataflow -> BigQuery) designed to handle millions of events per day.
