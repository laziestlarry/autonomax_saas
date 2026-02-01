# Architecture Overview

**MVP goal:** Stable SaaS backend with auth, projects, ops endpoints, and optional integrations.

## Components
- Cloud Run (FastAPI)
- Cloud SQL (Postgres)
- Secret Manager (secrets)
- Cloud Scheduler (cron jobs)
- Cloud Build (CI/CD)

## Design principles
- Stateless app containers
- DB as the source of truth
- Idempotent background jobs
- Clear boundaries: API / service / data access
