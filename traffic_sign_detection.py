import cv2
import requests
import os
import time
from config import STREAM_URL

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

# Function to safely load a classifier
def load_cascade(filename):
    if not os.path.exists(filename):
        print(f"Warning: Model file '{filename}' not found. Skipping this detector.")
        return None
    cascade = cv2.CascadeClassifier(filename)
    if cascade.empty():
        print(f"Error: Could not load '{filename}'. It might be corrupted.")
        return None
    return cascade

# Load Classifiers
yieldsign = load_cascade('yieldsign12Stages.xml')
Traffic_Light = load_cascade('TrafficLight_HAAR_16Stages.xml')
stop_sign = load_cascade('cascade_stop_sign.xml')
Speedlimit = load_cascade('Speedlimit_24_15Stages.xml')

# ======================================================================

def run_live_traffic_detection():
    stream_url = STREAM_URL
    snapshot_url = f"http://192.168.8.12/capture" 
    
    print(f"Connecting to stream: {stream_url}")
    cap = cv2.VideoCapture(stream_url)
    
    # Set a shorter timeout for OpenCV
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000000" 

    last_speak_time = 0
    AI_speak("Live traffic sign detection started.")

    while True:
        ret, frame = cap.read()
        
        # Fallback to snapshots if stream fails
        if not ret:
            try:
                resp = requests.get(snapshot_url, timeout=5)
                if resp.status_code == 200:
                    import numpy as np
                    nparr = np.frombuffer(resp.content, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                else:
                    time.sleep(1)
                    continue
            except Exception:
                time.sleep(2)
                cap.open(stream_url)
                continue

        if frame is None:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_label = None

        # 1. Stop Sign Detection
        if stop_sign:
            scales = stop_sign.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in scales:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 3)
                cv2.putText(frame, "Stop Sign", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                detected_label = "Stop Sign"

        # 2. Yield Sign Detection
        if yieldsign:
            scales = yieldsign.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in scales:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 3)
                cv2.putText(frame, "Yield Sign", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                detected_label = "Yield Sign"

        # 3. Traffic Light Detection
        if Traffic_Light:
            scales = Traffic_Light.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in scales:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                cv2.putText(frame, "Traffic Light", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                detected_label = "Traffic Light Red Stop"

        # 4. Speed Limit Detection
        if Speedlimit:
            scales = Speedlimit.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in scales:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 3)
                cv2.putText(frame, "Speed Limit", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                detected_label = "Speed Limit Sign"

        # Voice output (if something detected and 3 seconds passed)
        if detected_label and (time.time() - last_speak_time > 3):
            AI_speak(detected_label)
            last_speak_time = time.time()

        cv2.imshow('Live Traffic Sign Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_live_traffic_detection()
