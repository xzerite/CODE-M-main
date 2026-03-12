import requests
from config import CAMERA_IP
import socket

def check_port(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except:
        return False

def test_url(url):
    print(f"Trying: {url} ...", end=" ", flush=True)
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            print(f"SUCCESS! (Type: {content_type}, Size: {len(response.content)})")
            return True
        else:
            print(f"FAILED (404 Not Found)")
            return False
    except requests.exceptions.Timeout:
        print("TIMEOUT")
        return False
    except Exception as e:
        print(f"ERROR: {type(e).__name__}")
        return False

print(f"--- Diagnostic for ESP32-CAM at {CAMERA_IP} ---")

if check_port(CAMERA_IP, 80):
    print(f"[+] Port 80 is OPEN. Camera web server is running.")
else:
    print(f"[-] Port 80 is CLOSED. Check if the camera is powered on or if the IP is correct.")
    exit()

# List of common capture paths for different ESP32-CAM firmwares
paths = [
    "/capture",
    "/snapshot",
    "/jpg",
    "/pic",
    "/jpeg",
    "/stream",
    "/800x800.jpg",
    "/640x480.jpg",
    "/480x320.jpg"
]

found = []
for path in paths:
    url = f"http://{CAMERA_IP}{path}"
    if test_url(url):
        found.append(path)

print("\n--- Summary ---")
if found:
    print(f"Working paths found: {found}")
    print(f"\nPlease update CAMERA_URL_PATH in config.py to one of these.")
    print(f"Example: CAMERA_URL_PATH = \"{found[0]}\"")
else:
    print("No working image paths found.")
    print("Try opening http://" + CAMERA_IP + " in your browser to see the available settings.")
