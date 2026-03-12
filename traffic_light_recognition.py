# -*- coding: utf-8 -*-
"""
تعرف على إشارة المرور (أحمر/أخضر) - مأخوذ من A&H ومتكيف مع CODE-M
Traffic light recognition (red/green) - integrated with config and browser stream.
"""
import cv2
import threading
import subprocess
import sys
import os
import time
import struct
import socket
import numpy as np

# PyTorch 2.6+ defaults to weights_only=True; YOLO checkpoints need weights_only=False
try:
    import torch
    _orig_torch_load = torch.load
    def _torch_load(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return _orig_torch_load(*args, **kwargs)
    torch.load = _torch_load
except Exception:
    pass

from ultralytics import YOLO

from config import USE_DEVICE_CAMERA, STREAM_URL

# --- Audio Setup (قفل لمنع تداخل الأصوات) ---
engine = None
_speech_lock = threading.Lock()

try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    for voice in engine.getProperty("voices"):
        if "english" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break
except Exception:
    engine = None


def say_warning(text):
    """نطق التحذير بدون تداخل: صوت واحد في كل مرة."""
    def speak():
        with _speech_lock:
            if engine is not None:
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception:
                    pass
            elif sys.platform == "darwin":
                subprocess.run(["say", text], check=False)
    threading.Thread(target=speak, daemon=True).start()


# Load YOLO (yolov8n.pt from current dir or ultralytics cache)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_model_path = os.path.join(_script_dir, "yolov8n.pt")
if not os.path.isfile(_model_path):
    _model_path = "yolov8n.pt"
model = YOLO(_model_path)


def get_traffic_light_color(img):
    """Accurate HSV color masking for traffic lights."""
    try:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_red1 = np.array([0, 70, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 70, 50])
        upper_red2 = np.array([180, 255, 255])
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = mask_red1 + mask_red2
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([90, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        red_pixels = cv2.countNonZero(mask_red)
        green_pixels = cv2.countNonZero(mask_green)
        if red_pixels > green_pixels and red_pixels > 20:
            return "RED"
        if green_pixels > red_pixels and green_pixels > 20:
            return "GREEN"
    except Exception:
        pass
    return "UNKNOWN"


def main_system(source=0):
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

    cap = cv2.VideoCapture(source)
    if isinstance(source, str):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000000"
    last_voice_time = 0
    current_status = ""

    say_warning("Traffic light assistant ready. Please be careful crossing.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            if USE_DEVICE_CAMERA:
                time.sleep(0.1)
                continue
            time.sleep(1)
            cap.open(source)
            continue

        results = model(frame, conf=0.4, verbose=False)
        light_detected = False
        for r in results:
            for box in r.boxes:
                label = model.names[int(box.cls[0])]
                if label == "traffic light":
                    light_detected = True
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    pad = 5
                    y1_p = max(0, y1 - pad)
                    y2_p = min(frame.shape[0], y2 + pad)
                    x1_p = max(0, x1 - pad)
                    x2_p = min(frame.shape[1], x2 + pad)
                    light_img = frame[y1_p:y2_p, x1_p:x2_p]
                    if light_img.shape[0] > 0 and light_img.shape[1] > 0:
                        color = get_traffic_light_color(light_img)
                        display_color = (255, 255, 255)
                        msg = "Detecting..."
                        if color == "RED":
                            msg = "Red: Stop"
                            display_color = (0, 0, 255)
                            if current_status != "RED" or time.time() - last_voice_time > 4:
                                say_warning("Traffic light is Red for cars. It is safe to cross.")
                                last_voice_time = time.time()
                                current_status = "RED"
                        elif color == "GREEN":
                            msg = "Green: Wait"
                            display_color = (0, 255, 0)
                            if current_status != "GREEN" or time.time() - last_voice_time > 4:
                                say_warning("Stop! Traffic light is green for cars. Do not cross.")
                                last_voice_time = time.time()
                                current_status = "GREEN"
                        cv2.rectangle(frame, (x1, y1), (x2, y2), display_color, 3)
                        cv2.putText(frame, msg, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, display_color, 3)
        if not light_detected:
            current_status = ""

        cv2.putText(frame, "MODE: TRAFFIC LIGHT FOR BLIND", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        if stream_sock:
            try:
                _, jpeg = cv2.imencode(".jpg", frame)
                stream_sock.sendall(struct.pack(">I", len(jpeg)) + jpeg.tobytes())
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
        else:
            cv2.imshow("Traffic Light Recognition", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                say_warning("Traffic light system stopped.")
                break

    if stream_sock:
        try:
            stream_sock.close()
        except Exception:
            pass
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if USE_DEVICE_CAMERA:
        main_system(0)
    else:
        main_system(STREAM_URL)
