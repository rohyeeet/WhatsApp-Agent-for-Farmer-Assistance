#!/bin/bash

echo "🚀 Deploying Kisan Mitra to Google Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: 'gcloud' CLI is not found."
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Ask for Project ID if not set
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
else
    PROJECT_ID=$GOOGLE_CLOUD_PROJECT
    echo "✅ Using Project ID: $PROJECT_ID"
fi

# Enable necessary services
echo "🔄 Enabling Cloud Run and Container Registry APIs..."
gcloud services enable run.googleapis.com containerregistry.googleapis.com

# Deploy
echo "📦 Building and Deploying..."
gcloud run deploy kisan-mitra-bot \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8000 \
    --set-env-vars "$(cat .env | grep -v '^#' | xargs | sed 's/ /,/g')"

echo "✅ Deployment Complete!"
echo "🌍 Your Service URL is displayed above."
echo "👉 Don't forget to update your Twilio Webhook URL!"
