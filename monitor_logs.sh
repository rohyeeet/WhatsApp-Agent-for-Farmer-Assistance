#!/bin/bash

# 📊 Kisan Mitra - Real-time Log Monitor
# This script shows all system activity in real-time

echo "📊 Kisan Mitra - Real-time Log Monitor"
echo "======================================="
echo "🌾 ADK Server Logs | 📱 WhatsApp Logs | 🌐 ngrok Logs"
echo "======================================="
echo ""

# Function to monitor logs with colored output
monitor_logs() {
    # Use multitail if available, otherwise use tail
    if command -v multitail &> /dev/null; then
        echo "✅ Using multitail for enhanced monitoring..."
        multitail -l "tail -f adk_server.log" -l "tail -f whatsapp_server.log" -l "tail -f ngrok.log"
    else
        echo "📝 Using basic tail monitoring (install multitail for better experience)..."
        echo "   brew install multitail  # On macOS"
        echo ""
        echo "🔄 Monitoring WhatsApp Server logs (most important for voice debugging)..."
        echo "   Press Ctrl+C to stop"
        echo ""
        tail -f whatsapp_server.log
    fi
}

# Check if log files exist
if [ ! -f "whatsapp_server.log" ]; then
    echo "❌ whatsapp_server.log not found. Start the system first:"
    echo "   ./start_kisan_mitra_whatsapp.sh"
    exit 1
fi

# Start monitoring
monitor_logs 