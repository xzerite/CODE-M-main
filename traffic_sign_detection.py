import cv2
import requests
import os
import time
import struct
import socket
import numpy as np
from config import STREAM_URL, CAMERA_IP, USE_DEVICE_CAMERA

# ======================================================================
engine = None
try:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    voice_index = 1 if len(voices) > 1 else 0
    engine.setProperty('voice', voices[voice_index].id)
    engine.setProperty("rate", 140)
except Exception:
    pass

def AI_speak(label):
    if engine:
        try:
            engine.say(label)
            engine.runAndWait()
        except Exception:
            print(label)
    else:
        print(label)
    return label

# ======================================================================

def load_cascade(filename):
    # Check current directory FIRST, then script directory
    search_paths = [
        filename,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    ]
    
    for full_path in search_paths:
        if os.path.exists(full_path) and os.path.getsize(full_path) > 100:
            cascade = cv2.CascadeClassifier(full_path)
            if not cascade.empty():
                print(f"Success: Loaded model '{filename}' from {full_path}")
                return cascade
    
    print(f"Warning: Could not find or load model '{filename}'. Check if the file exists and is not empty.")
    return None

# Load Classifiers
print("--- Loading Models ---")
yieldsign = load_cascade('yieldsign12Stages.xml')
Traffic_Light = load_cascade('TrafficLight_HAAR_16Stages.xml')
stop_sign = load_cascade('cascade_stop_sign.xml')
Speedlimit = load_cascade('Speedlimit_24_15Stages.xml')
print("----------------------")

# ======================================================================

def run_live_traffic_detection():
    stream_sock = None
    stream_to_browser = os.environ.get("STREAM_TO_BROWSER") == "1"
    stream_port = os.environ.get("STREAM_PORT")
    if stream_to_browser and stream_port:
        try:
            stream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            stream_sock.connect(("127.0.0.1", int(stream_port)))
        except Exception as e:
            print(f"Stream to browser failed: {e}")
            stream_sock = None

    if USE_DEVICE_CAMERA:
        print("Using device camera (0)")
        cap = cv2.VideoCapture(0)
        snapshot_url = None
    else:
        stream_url = STREAM_URL
        snapshot_url = f"http://{CAMERA_IP}/capture"
        print(f"Connecting to stream: {stream_url}")
        cap = cv2.VideoCapture(stream_url)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)

    last_speak_time = 0
    AI_speak("Live traffic sign detection started.")

    while True:
        ret, frame = cap.read()

        if not ret and USE_DEVICE_CAMERA:
            time.sleep(0.1)
            continue
        # Fallback to snapshots if stream fails or times out
        if not ret and snapshot_url:
            try:
                resp = requests.get(snapshot_url, timeout=3)
                if resp.status_code == 200:
                    nparr = np.frombuffer(resp.content, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        # Draw fallback indicator
                        cv2.putText(frame, "Snapshot Mode", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                else:
                    time.sleep(1)
                    continue
            except Exception:
                print("Stream timed out. Retrying...")
                time.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(STREAM_URL)
                continue

        if frame is None:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_label = None

        # 1. Stop Sign 
        if stop_sign is not None:
            signs = stop_sign.detectMultiScale(gray, 1.1, 5)
            for (x, y, w, h) in signs:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 3)
                cv2.putText(frame, "STOP", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                detected_label = "Stop Sign Detected"

        # 2. Yield Sign
        if yieldsign is not None:
            signs = yieldsign.detectMultiScale(gray, 1.1, 5)
            for (x, y, w, h) in signs:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 3)
                cv2.putText(frame, "YIELD", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
                detected_label = "Yield Sign"

        # 3. Traffic Light
        if Traffic_Light is not None:
            signs = Traffic_Light.detectMultiScale(gray, 1.1, 5)
            for (x, y, w, h) in signs:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                cv2.putText(frame, "Traffic Light", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                detected_label = "Traffic Light Ahead"

        # 4. Speed Limit
        if Speedlimit is not None:
            signs = Speedlimit.detectMultiScale(gray, 1.1, 5)
            for (x, y, w, h) in signs:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 3)
                cv2.putText(frame, "Speed Limit", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                detected_label = "Speed Limit Sign"

        # Voice feedback every 4 seconds
        if detected_label and (time.time() - last_speak_time > 4):
            AI_speak(detected_label)
            last_speak_time = time.time()

        if stream_sock:
            try:
                _, jpeg = cv2.imencode(".jpg", frame)
                stream_sock.sendall(struct.pack(">I", len(jpeg)) + jpeg.tobytes())
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
        else:
            cv2.imshow("Traffic Detection (Press Q to quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if stream_sock:
        try:
            stream_sock.close()
        except Exception:
            pass
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_live_traffic_detection()
