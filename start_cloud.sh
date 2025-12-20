#!/bin/bash
# Run in background but keep output visible for Cloud Logging
adk api_server --host 0.0.0.0 --port 8001 --no-reload . &

echo "Waiting 10s for ADK Agent..."
sleep 10

echo "Starting WhatsApp Uvicorn Server on PORT $PORT..."
# Bind uvicorn to the PORT environment variable provided by Cloud Run
exec uvicorn whatsapp_kisan_mitra:app --host 0.0.0.0 --port $PORT --log-level debug
