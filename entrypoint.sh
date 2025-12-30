#!/bin/bash
set -e

# Start the ADK Server in the background
# Start the ADK Server - CLOUD RUN FIX
# Cloud Run filesystem is read-only, so we must run ADK in /tmp
# Copy everything (including hidden files) to /tmp
cp -a /app/. /tmp/adk_home/
cd /tmp/adk_home

# Run the services manager (handles ADK and WhatsApp piping logs)
echo "🚀 Launching Runner..."
exec python runner.py
