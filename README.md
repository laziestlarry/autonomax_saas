# Autonomax SaaS Starter (Cloud Run + Cloud Build)

This repo is a **clean, repeatable “golden path”** for a production-ready FastAPI SaaS backend on **Google Cloud Run**.

It intentionally avoids flags your `gcloud` doesn't support (like `--dockerfile`) by using a Cloud Build YAML.

## What you get

- FastAPI app with:
  - `/healthz` and `/readyz`
  - Auth (register/login) with JWT
  - Admin-protected ops routes:
    - `POST /api/ops/run`
    - `POST /api/ops/run/ledger-monitor`
    - `POST /api/ops/run/shopier-verify`
  - Simple rate-limit locks (prevents accidental double runs)
- SQLAlchemy DB (Postgres or SQLite fallback)
- Cloud Build config: `cloudbuild.autonomax-api.yaml`
- Cloud Run deploy script: `scripts/deploy_autonomax_api.sh`
- `.gcloudignore` to keep builds fast

---

## 0) Prereqs

- GCP project set: `propulse-autonomax`
- Cloud Run API + Cloud Build API enabled
- Secrets exist in Secret Manager:
  - `youtube-ai-database-url` (DATABASE_URL)
  - `youtube-ai-security-secret-key` (SECRET_KEY / SECURITY_SECRET_KEY)
  - `autonomax-admin-secret-key` (ADMIN_SECRET_KEY)

> Tip: Use Cloud SQL on Cloud Run via mounted instance + DATABASE_URL using `/cloudsql/...` socket.
> Example format:
> `postgresql+psycopg2://USER:PASSWORD@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`

---

## 1) Build & push image (repeatable)

From repo root:

```bash
PROJECT="propulse-autonomax"
TAG="autonomax-api-$(date +%Y%m%d-%H%M%S)"
IMAGE="gcr.io/${PROJECT}/autonomax-api:${TAG}"

gcloud builds submit   --project "${PROJECT}"   --config cloudbuild.autonomax-api.yaml   --substitutions _IMAGE="${IMAGE}"   .
```

---

## 2) Deploy canary (no traffic) then test

```bash
PROJECT="propulse-autonomax"
REGION="us-central1"

gcloud run deploy autonomax-api   --project "${PROJECT}"   --region "${REGION}"   --image "${IMAGE}"   --no-traffic   --tag canary   --concurrency 40   --cpu 1   --memory 1Gi   --timeout 300   --max-instances 2   --min-instances 0   --add-cloudsql-instances "propulse-autonomax:us-central1:youtube-ai-db"   --set-secrets "DATABASE_URL=youtube-ai-database-url:latest"   --set-secrets "SECRET_KEY=youtube-ai-security-secret-key:latest"   --set-secrets "SECURITY_SECRET_KEY=youtube-ai-security-secret-key:latest"   --set-secrets "ADMIN_SECRET_KEY=autonomax-admin-secret-key:latest"
```

Tagged URL looks like:
`https://canary---autonomax-api-<hash>-uc.a.run.app`

Test ops endpoint:

```bash
CANARY_URL="https://canary---autonomax-api-<hash>-uc.a.run.app"
curl -i -X POST -H "X-Admin-Key: YOUR_ADMIN_SECRET" "$CANARY_URL/api/ops/run"
```

---

## 3) Promote to 100%

```bash
gcloud run services update-traffic autonomax-api   --project "${PROJECT}"   --region "${REGION}"   --to-tags canary=100
```

---

## Scheduler compatibility

Cloud Scheduler often sends **no body**. This template accepts empty bodies for `POST /api/ops/run` by design.

---

## Local run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r services/autonomax_api/requirements.txt
export SECRET_KEY="dev-secret"
export ADMIN_SECRET_KEY="dev-admin"
uvicorn services.autonomax_api.main:app --reload --port 8080
```
# autonomax_saas
