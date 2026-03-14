import cv2
import requests
import os
import time
import struct
import socket
from config import STREAM_URL, CAMERA_IP, USE_DEVICE_CAMERA, open_stream_capture

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

def AI_speak(something):
    if engine:
        try:
            engine.say(something)
            engine.runAndWait()
        except Exception:
            print(something)
    else:
        print(something)
    return something

# ======================================================================

def get_color_name(hsv_pixel):
    hue_value = hsv_pixel[0]
    saturation = hsv_pixel[1]
    value = hsv_pixel[2]

    color = "Undefined"
    if saturation < 20:
        if value > 200:
            color = "White"
        else:
            color = "Gray" if value > 50 else "Black"
    elif hue_value < 5 or hue_value > 175:
        color = "Red"
    elif hue_value < 22:
        color = "Orange"
    elif hue_value < 33:
        color = "Yellow"
    elif hue_value < 78:
        color = "Green"
    elif hue_value < 130:
        color = "Blue"
    elif hue_value < 170:
        color = "Magenta"
    else:
        color = "Purple"

    # Refine colors
    if color == "Magenta" and value > 200:
        color = "Pink"
    if color == "Red" and value < 50:
        color = "Maroon"
    if color == "Orange" and value < 100:
        color = "Brown"
        
    return color

# ======================================================================

# ======================================================================

def run_live_detection():
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
        snapshot_url = f"http://{CAMERA_IP}/capture"
        print("Connecting to camera stream...")
        cap = open_stream_capture()
        if cap is None:
            print("Could not open stream. Check IP (e.g. 192.168.8.12), port 80, and that camera is on.")
            return

    last_speak_time = 0

    while True:
        ret, frame = cap.read()

        if not ret and USE_DEVICE_CAMERA:
            time.sleep(0.1)
            continue
        # If stream fails, try to reconnect or use snapshots
        if not ret and snapshot_url:
            print("Stream interrupted. Falling back to snapshot mode...")
            try:
                resp = requests.get(snapshot_url, timeout=5)
                if resp.status_code == 200:
                    import numpy as np
                    nparr = np.frombuffer(resp.content, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                else:
                    time.sleep(1)
                    continue
            except Exception as e:
                print(f"Connection error: {e}")
                time.sleep(2)
                cap.open(STREAM_URL)
                continue

        if frame is None:
            continue

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        height, width, _ = frame.shape

        cx = int(width / 2)
        cy = int(height / 2)

        # Pick pixel value at center
        pixel_center = hsv_frame[cy, cx]
        current_color = get_color_name(pixel_center)

        # Speak the color every 3 seconds
        if time.time() - last_speak_time > 3:
            AI_speak(current_color)
            last_speak_time = time.time()

        # Draw UI
        pixel_center_bgr = frame[cy, cx]
        b, g, r = int(pixel_center_bgr[0]), int(pixel_center_bgr[1]), int(pixel_center_bgr[2])
        
        cv2.putText(frame, current_color, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (b, g, r), 3)
        cv2.circle(frame, (cx, cy), 15, (255, 255, 255), 2)

        if stream_sock:
            try:
                _, jpeg = cv2.imencode(".jpg", frame)
                stream_sock.sendall(struct.pack(">I", len(jpeg)) + jpeg.tobytes())
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
        else:
            cv2.imshow("Live Color Detection", frame)
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
    run_live_detection()
