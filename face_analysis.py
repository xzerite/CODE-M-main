# -*- coding: utf-8 -*-
"""
تحليل الوجه (عمر، جنس، انفعال) - مأخوذ من A&H ومتكيف مع CODE-M
Face analysis (age, gender, emotion) - DeepFace + config + browser stream.
"""
import cv2
import threading
import subprocess
import sys
import os
import time
import struct
import socket

from config import USE_DEVICE_CAMERA, STREAM_URL

# --- Audio ---
engine = None
try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    for voice in engine.getProperty("voices"):
        if "english" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break
except Exception:
    engine = None

_speech_lock = threading.Lock()

def say_text(text):
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
    if threading.active_count() <= 8:
        threading.Thread(target=speak, daemon=True).start()

# Tracking
face_info = "Analyzing..."
last_analysis_time = 0
last_voice_time = 0

# Haar Cascade
face_cascade = None

def _get_face_cascade():
    global face_cascade
    if face_cascade is not None:
        return face_cascade
    try:
        path = getattr(cv2.data, "haarcascades", None)
        if path:
            path = os.path.join(path, "haarcascade_frontalface_default.xml")
        if not path or not os.path.isfile(path):
            path = os.path.join(os.path.dirname(cv2.__file__), "data", "haarcascade_frontalface_default.xml")
        if os.path.isfile(path):
            face_cascade = cv2.CascadeClassifier(path)
    except Exception:
        face_cascade = False
    return face_cascade


def analyze_face_async(face_crop):
    global face_info, last_voice_time
    try:
        from deepface import DeepFace
        results = DeepFace.analyze(face_crop, actions=["age", "gender", "emotion"],
                                  enforce_detection=False, silent=True)
        res = results[0]
        face_info = f"{res['dominant_gender']}, {res['age']}y, {res['dominant_emotion']}"
        gender = "man" if str(res["dominant_gender"]).lower() == "man" else "woman"
        spoken_text = f"I see a {gender} facing you, around {res['age']} years old, who looks {res['dominant_emotion']}."
        if time.time() - last_voice_time > 6.0:
            print(spoken_text)
            say_text(spoken_text)
            last_voice_time = time.time()
    except Exception:
        pass


def main_system(source=0):
    global face_info, last_analysis_time

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

    cascade = _get_face_cascade()
    if cascade is None or cascade is False:
        print("Error: Could not load face cascade.")
        cap.release()
        return

    say_text("Face reading system is active.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            if USE_DEVICE_CAMERA:
                time.sleep(0.1)
                continue
            time.sleep(1)
            cap.open(source)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

        if len(faces) > 0:
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, w, h = faces[0]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 100, 0), 2)
            cv2.putText(frame, face_info, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            if time.time() - last_analysis_time > 1.5:
                face_crop = frame[y:y + h, x:x + w]
                if face_crop.size > 0:
                    threading.Thread(target=analyze_face_async, args=(face_crop.copy(),), daemon=True).start()
                    last_analysis_time = time.time()

        cv2.putText(frame, "MODE: BLIND FACE ANALYSIS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if stream_sock:
            try:
                _, jpeg = cv2.imencode(".jpg", frame)
                stream_sock.sendall(struct.pack(">I", len(jpeg)) + jpeg.tobytes())
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
        else:
            cv2.imshow("Face Analysis for Visually Impaired", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                say_text("Face reading stopped.")
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
