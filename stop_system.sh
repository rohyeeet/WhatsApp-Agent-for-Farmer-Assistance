#!/bin/bash

echo "🛑 Stopping Kisan Mitra WhatsApp System..."

# Stop processes using PIDs
if [ -f .adk_pid ]; then
    ADK_PID=$(cat .adk_pid)
    if kill -0 $ADK_PID 2>/dev/null; then
        kill $ADK_PID
        echo "✅ Stopped ADK API server (PID: $ADK_PID)"
    fi
    rm -f .adk_pid
fi

if [ -f .whatsapp_pid ]; then
    WHATSAPP_PID=$(cat .whatsapp_pid)
    if kill -0 $WHATSAPP_PID 2>/dev/null; then
        kill $WHATSAPP_PID
        echo "✅ Stopped WhatsApp server (PID: $WHATSAPP_PID)"
    fi
    rm -f .whatsapp_pid
fi

if [ -f .ngrok_pid ]; then
    NGROK_PID=$(cat .ngrok_pid)
    if kill -0 $NGROK_PID 2>/dev/null; then
        kill $NGROK_PID
        echo "✅ Stopped ngrok (PID: $NGROK_PID)"
    fi
    rm -f .ngrok_pid
fi

# Force kill any remaining processes
pkill -f "adk_api_server.py" 2>/dev/null && echo "🔥 Force stopped ADK API server"
pkill -f "whatsapp_kisan_mitra.py" 2>/dev/null && echo "🔥 Force stopped WhatsApp server"
pkill -f "ngrok" 2>/dev/null && echo "🔥 Force stopped ngrok"

# Clean up log files
rm -f adk_server.log whatsapp_server.log ngrok.log 2>/dev/null

echo "✅ All services stopped successfully!" 