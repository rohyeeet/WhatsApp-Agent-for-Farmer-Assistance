import subprocess
import os
import sys
import time
import threading

def pipe_output(process, name):
    for line in iter(process.stdout.readline, b''):
        sys.stdout.write(f'[{name}] {line.decode()}')
        sys.stdout.flush()
    process.stdout.close()

def start_services():
    print("🚀 Starting Kisan Mitra Services Manager v10 (Voice Fixes)...", flush=True)
    
    # 1. Start ADK API Server
    print("🧠 Starting ADK AI Brain (Port 8001)...")
    try:
        # Check if 'adk' exists
        result = subprocess.run(["which", "adk"], capture_output=True, text=True)
        print(f"DEBUG: 'which adk' returned: {result.stdout.strip()}")
        
        adk_process = subprocess.Popen(
            ["adk", "api_server", "--host", "0.0.0.0", "--port", "8001", "--no-reload", "."],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd="/tmp/adk_home"
        )
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to launch ADK process: {e}")
        sys.exit(1)
    
    # Start thread to pipe ADK output
    adk_thread = threading.Thread(target=pipe_output, args=(adk_process, "ADK"))
    adk_thread.daemon = True
    adk_thread.start()
    
    # Give ADK a moment to start
    time.sleep(5)
    
    # 2. Start WhatsApp Gateway
    print("📱 Starting WhatsApp Gateway (Port 8000)...")
    whatsapp_process = subprocess.Popen(
        ["python", "whatsapp_kisan_mitra.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd="/tmp/adk_home"
    )
    
    # Start thread to pipe WhatsApp output
    whatsapp_thread = threading.Thread(target=pipe_output, args=(whatsapp_process, "WA"))
    whatsapp_thread.daemon = True
    whatsapp_thread.start()
    
    print("✅ Both services triggered. Monitoring...")
    
    # Keep main process alive while services are running
    try:
        while True:
            if adk_process.poll() is not None:
                print(f"❌ ADK Server exited with code {adk_process.returncode}")
                # Optional: Restart or Exit
                sys.exit(1)
            if whatsapp_process.poll() is not None:
                print(f"❌ WhatsApp Gateway exited with code {whatsapp_process.returncode}")
                sys.exit(1)
            time.sleep(5)
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
        adk_process.terminate()
        whatsapp_process.terminate()

if __name__ == "__main__":
    start_services()
