#!/bin/bash

# 🌾 Kisan Mitra WhatsApp - Complete Startup Script
# This script starts everything and gives you the ngrok link for Twilio

set -e  # Exit on any error

echo "🌾 Starting Kisan Mitra WhatsApp System..."
echo "======================================="

# Load environment variables
if [ -f .env ]; then
    source .env
    echo "✅ Environment variables loaded"
else
    echo "❌ .env file not found!"
    exit 1
fi

# Function to check if a process is running
check_process() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    echo "⏳ Waiting for $name to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $name is ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo "❌ $name failed to start within $max_attempts seconds"
    return 1
}

# Clean up any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "adk api_server" || true
pkill -f "whatsapp_kisan_mitra.py" || true
pkill -f "ngrok" || true
sleep 2

# Install dependencies if needed
if ! command -v adk &> /dev/null; then
    echo "📦 Installing ADK dependencies..."
    pip install -r requirements.txt
fi

# Start ADK API Server
echo "🌾 Starting ADK API Server..."
nohup adk api_server --host 0.0.0.0 --port 8001 --no-reload . > adk_server.log 2>&1 &
ADK_PID=$!
echo $ADK_PID > .adk_pid
echo "✅ ADK API server started (PID: $ADK_PID)"

# Wait for ADK server
wait_for_service "http://localhost:8001/" "ADK API Server"

# Start WhatsApp Server
echo "📱 Starting WhatsApp Server..."
nohup python3 whatsapp_kisan_mitra.py > whatsapp_server.log 2>&1 &
WHATSAPP_PID=$!
echo $WHATSAPP_PID > .whatsapp_pid
echo "✅ WhatsApp server started (PID: $WHATSAPP_PID)"

# Wait for WhatsApp server
wait_for_service "http://localhost:8000/health" "WhatsApp Server"

# Start ngrok
echo "🌐 Starting ngrok tunnel..."
nohup ngrok http 8000 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!
echo $NGROK_PID > .ngrok_pid
echo "✅ ngrok started (PID: $NGROK_PID)"

# Wait for ngrok to establish tunnel
echo "⏳ Waiting for ngrok tunnel to establish..."
sleep 5

# Extract ngrok URL
NGROK_URL=""
for i in {1..30}; do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    for tunnel in tunnels:
        if tunnel.get('config', {}).get('addr') == 'http://localhost:8000':
            print(tunnel['public_url'])
            break
except:
    pass
" 2>/dev/null)
    
    if [ ! -z "$NGROK_URL" ]; then
        break
    fi
    sleep 1
done

# Display results
echo ""
echo "🎉 System Started Successfully!"
echo "================================"
echo "🌾 ADK API Server: http://localhost:8001"
echo "📱 WhatsApp Server: http://localhost:8000"

if [ ! -z "$NGROK_URL" ]; then
    echo "🌐 ngrok Public URL: $NGROK_URL"
    echo ""
    echo "📋 FOR TWILIO WEBHOOK CONFIGURATION:"
    echo "======================================"
    echo "🔗 WEBHOOK URL: $NGROK_URL/webhook/whatsapp"
    echo ""
    echo "📋 Copy this URL and paste it in your Twilio WhatsApp Sandbox webhook configuration."
else
    echo "❌ Failed to get ngrok URL. Check ngrok.log for details."
fi

echo ""
echo "🧪 Test Commands:"
echo "================"
echo "Health Check: curl $NGROK_URL/health"
echo "Test Message: curl -X POST \"$NGROK_URL/test/message?message=hello&phone=%2B919876543210\""
echo ""
echo "📊 Monitor Logs:"
echo "==============="
echo "ADK Server: tail -f adk_server.log"
echo "WhatsApp Server: tail -f whatsapp_server.log"
echo "ngrok: tail -f ngrok.log"
echo ""
echo "🛑 Stop All Services:"
echo "===================="
echo "./stop_system.sh"
echo ""

# Save the URLs to a file for easy access
cat > .system_urls << EOF
ADK_API_URL=http://localhost:8001
WHATSAPP_URL=http://localhost:8000
NGROK_URL=$NGROK_URL
WEBHOOK_URL=$NGROK_URL/webhook/whatsapp
EOF

echo "💾 URLs saved to .system_urls file"
echo ""
echo "🚀 Ready to receive WhatsApp messages from farmers!"

# Final health check
echo "🔍 Final Health Check:"
echo "====================="
if curl -s "http://localhost:8001/" > /dev/null; then
    echo "✅ ADK API: Healthy"
else
    echo "❌ ADK API: Not responding"
fi

if curl -s "http://localhost:8000/health" > /dev/null; then
    echo "✅ WhatsApp Server: Healthy"
else
    echo "❌ WhatsApp Server: Not responding"
fi

if [ ! -z "$NGROK_URL" ] && curl -s "$NGROK_URL/health" > /dev/null; then
    echo "✅ ngrok Tunnel: Healthy"
else
    echo "❌ ngrok Tunnel: Not responding"
fi

echo ""
echo "🌾 Kisan Mitra WhatsApp is ready! 🌾" 