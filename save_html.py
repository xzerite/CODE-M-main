import requests
try:
    r = requests.get('http://192.168.8.12', timeout=5)
    with open('camera_index.html', 'wb') as f:
        f.write(r.content)
    print("SAVED")
except Exception as e:
    print(f"ERROR: {e}")
