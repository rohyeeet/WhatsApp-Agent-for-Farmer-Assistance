import subprocess
import os
import sys
import time
import threading

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ADK_BIN = os.path.expanduser('~/Library/Python/3.9/bin/adk')

def pipe_output(process, name):
    for line in iter(process.stdout.readline, b''):
        sys.stdout.write(f'[{name}] {line.decode()}')
        sys.stdout.flush()
    process.stdout.close()

def start_services():
    print("🚀 Starting Kisan Mitra Services Manager...", flush=True)

    adk_cmd = ADK_BIN if os.path.exists(ADK_BIN) else 'adk'

    # 1. Start ADK API Server
    print("🧠 Starting ADK AI Brain (Port 8001)...")
    try:
        adk_process = subprocess.Popen(
            [adk_cmd, "api_server", "--host", "0.0.0.0", "--port", "8001", "--no-reload", "."],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=PROJECT_DIR
        )
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to launch ADK process: {e}")
        sys.exit(1)

    adk_thread = threading.Thread(target=pipe_output, args=(adk_process, "ADK"))
    adk_thread.daemon = True
    adk_thread.start()

    time.sleep(5)

    # 2. Start WhatsApp Gateway
    print("📱 Starting WhatsApp Gateway (Port 8000)...")
    whatsapp_process = subprocess.Popen(
        [sys.executable, "whatsapp_kisan_mitra.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=PROJECT_DIR
    )

    whatsapp_thread = threading.Thread(target=pipe_output, args=(whatsapp_process, "WA"))
    whatsapp_thread.daemon = True
    whatsapp_thread.start()

    print("✅ Both services triggered. Monitoring...")

    try:
        while True:
            if adk_process.poll() is not None:
                print(f"❌ ADK Server exited with code {adk_process.returncode}")
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
