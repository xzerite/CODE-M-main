# -*- coding: utf-8 -*-
"""
قراءة النص (OCR) - مأخوذ من A&H ومتكيف مع CODE-M. EasyOCR + بث في المتصفح.
Text recognition for blind - config + browser stream.
"""
import cv2
import os
import time
import struct
import socket
import threading

from config import USE_DEVICE_CAMERA, STREAM_URL

# --- Audio ---
engine = None
try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 140)
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
    if threading.active_count() <= 8:
        threading.Thread(target=speak, daemon=True).start()

# EasyOCR - تحميل عند أول استخدام
reader = None

def _get_reader():
    global reader
    if reader is not None:
        return reader
    try:
        import easyocr
        reader = easyocr.Reader(["en"])
    except Exception as e:
        print(f"EasyOCR load error: {e}")
    return reader

# State
detected_text = ""
last_analysis_time = 0
last_spoken_text = ""


def analyze_text_async(frame_copy):
    global detected_text, last_spoken_text
    r = _get_reader()
    if r is None:
        return
    try:
        results = r.readtext(frame_copy, detail=0, paragraph=True)
        new_text = " ".join(results).strip()
        if new_text and len(new_text) > 3:
            detected_text = new_text
            if new_text != last_spoken_text:
                print(f"Reading: {detected_text}")
                say_text(f"Text says: {detected_text}")
                last_spoken_text = new_text
    except Exception:
        pass


def main_system(source=0):
    global detected_text, last_analysis_time

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

    say_text("Text reader active. Please point the camera at any text.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            if USE_DEVICE_CAMERA:
                time.sleep(0.1)
                continue
            time.sleep(1)
            cap.open(source)
            continue

        height, width = frame.shape[:2]

        if time.time() - last_analysis_time > 3.0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            enhanced = cv2.equalizeHist(gray)
            enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            threading.Thread(target=analyze_text_async, args=(enhanced_rgb.copy(),), daemon=True).start()
            last_analysis_time = time.time()

        cv2.rectangle(frame, (0, height - 60), (width, height), (0, 0, 0), -1)
        disp_text = (detected_text[:60] + "...") if len(detected_text) > 60 else detected_text
        cv2.putText(frame, disp_text, (10, height - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "MODE: TEXT READER FOR BLIND", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        if stream_sock:
            try:
                _, jpeg = cv2.imencode(".jpg", frame)
                stream_sock.sendall(struct.pack(">I", len(jpeg)) + jpeg.tobytes())
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
        else:
            cv2.imshow("Text Recognition", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                say_text("Text reader stopped.")
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
