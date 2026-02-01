#!/usr/bin/env bash
set -euo pipefail

PROJECT="${PROJECT:-propulse-autonomax}"
REGION="${REGION:-us-central1}"
TAG="autonomax-api-$(date +%Y%m%d-%H%M%S)"
IMAGE="gcr.io/${PROJECT}/autonomax-api:${TAG}"

echo "Building: ${IMAGE}"
gcloud builds submit   --project "${PROJECT}"   --config cloudbuild.autonomax-api.yaml   --substitutions _IMAGE="${IMAGE}"   .

echo "Deploying canary (no traffic)..."
gcloud run deploy autonomax-api   --project "${PROJECT}"   --region "${REGION}"   --image "${IMAGE}"   --no-traffic   --tag canary   --concurrency 40   --cpu 1   --memory 1Gi   --timeout 300   --max-instances 2   --min-instances 0   --add-cloudsql-instances "propulse-autonomax:us-central1:youtube-ai-db"   --set-secrets "DATABASE_URL=youtube-ai-database-url:latest"   --set-secrets "SECRET_KEY=youtube-ai-security-secret-key:latest"   --set-secrets "SECURITY_SECRET_KEY=youtube-ai-security-secret-key:latest"   --set-secrets "ADMIN_SECRET_KEY=autonomax-admin-secret-key:latest"

echo
echo "Canary deployed. Find tagged URL in the command output."
echo "Promote with:"
echo "  gcloud run services update-traffic autonomax-api --project ${PROJECT} --region ${REGION} --to-tags canary=100"
