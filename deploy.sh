#!/usr/bin/env bash
set -e

PROJECT_ID="arsanjani-genai"
REGION="us-central1"
SERVICE_NAME="promo-sim-agent-engine"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "=========================================================="
echo "🚀 Deploying PROMO-SIM to Google Cloud Agent Engine / Run"
echo "Project: ${PROJECT_ID} | Region: ${REGION}"
echo "=========================================================="

echo "📦 1. Building and submitting container image via Cloud Build..."
gcloud builds submit --project="${PROJECT_ID}" --tag="${IMAGE_TAG}" .

echo "🚢 2. Deploying service to Cloud Run / Agent Engine runtime..."
gcloud run deploy "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --image="${IMAGE_TAG}" \
    --platform="managed" \
    --region="${REGION}" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}" \
    --memory="2Gi" \
    --cpu="2" \
    --timeout="3600"

echo "✅ 3. Fetching service URL..."
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --project="${PROJECT_ID}" --region="${REGION}" --format='value(status.url)')

echo "=========================================================="
echo "🎉 Deployment Complete!"
echo "Service Live URL: ${SERVICE_URL}"
echo "=========================================================="
