import sys
import os
import subprocess
import time
import socket
import threading
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from config.settings import get_settings

settings = get_settings()
PORT = settings.server.PORT

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def kill_port(port):
    try:
        result = subprocess.run(f'netstat -ano | findstr :{port}', capture_output=True, text=True, shell=True)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'LISTENING' in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p.isdigit() and i > 0 and parts[i-1] == 'LISTENING':
                        subprocess.run(f'taskkill /PID {p} /F', capture_output=True, shell=True)
                        break
    except:
        pass

def start_server():
    import uvicorn
    from app.main import app
    
    global PORT
    
    if check_port(PORT):
        kill_port(PORT)
        time.sleep(1)
    
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_config=None)

if __name__ == "__main__":
    print("=" * 50)
    print("   Doc2PDF")
    print("=" * 50)
    print(f"\n[INFO] Starting server...")
    
    if check_port(PORT):
        kill_port(PORT)
        time.sleep(1)
    
    threading.Thread(target=start_server, daemon=True).start()
    
    for i in range(20):
        time.sleep(0.3)
        if check_port(PORT):
            print(f"[OK] Server ready!")
            break
    
    time.sleep(0.5)
    webbrowser.open(f'http://localhost:{PORT}')
    
    print("\n" + "=" * 50)
    print("Server running. Press Ctrl+C to stop.")
    print("=" * 50)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        sys.exit(0)
