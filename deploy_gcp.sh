#!/bin/bash
# Deployment script for Kisan Mitra on Google Cloud Run

set -e

# Load environment variables from .env
if [ -f .env ]; then
    echo "🔑 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️ .env file not found/loaded!"
fi

PROJECT_ID=$(gcloud config get-value project)
REGION="asia-south1" 
SERVICE_NAME="kisan-mitra-bot"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Deploying Kisan Mitra to Google Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# 1. Build and Push Image
echo "🔨 Building Container Image..."
gcloud builds submit --tag $IMAGE_NAME .

# 2. Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
# We explicitly pass the critical API keys and timeout
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --timeout=300 \
    --set-env-vars="TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID,TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN,TWILIO_PHONE_NUMBER=$TWILIO_PHONE_NUMBER,GOOGLE_API_KEY=$GOOGLE_API_KEY,ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY"

echo "✅ Deployment Complete!"
echo "Get your Service URL from the output above and update Twilio Webhook."
