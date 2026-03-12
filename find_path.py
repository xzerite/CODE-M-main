import requests
from config import CAMERA_IP

paths = ["/capture", "/snapshot", "/jpg", "/pic", "/jpeg", "/800x800.jpg", "/640x480.jpg"]
found_path = None

for path in paths:
    url = f"http://{CAMERA_IP}{path}"
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            found_path = path
            break
    except:
        continue

if found_path:
    print(f"FOUND:{found_path}")
else:
    print("NOT_FOUND")
