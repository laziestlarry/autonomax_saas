# Operations Runbook

## Health checks
- GET /healthz
- GET /readyz

## Deploy
- Cloud Build produces an image
- Cloud Run deploys with secrets + Cloud SQL binding

## Debugging
- Cloud Run logs: startup, migrations, request errors
- DB: connection issues, migrations, slow queries

## Rollback
- Cloud Run revisions → shift traffic back
