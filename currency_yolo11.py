# -*- coding: utf-8 -*-
"""
كشف العملات - YOLOv11 | سرعة البرق على أجهزة الجوال
متكيف مع CODE-M: مصدر الكاميرا من config.
يدعم نموذج مخصص للعملات إن وُجد (مثلاً weights/currency_yolo11.pt).
"""
import os
import cv2
import numpy as np
import requests
from config import USE_DEVICE_CAMERA, CAMERA_URL, capture_from_device

script_dir = os.path.dirname(os.path.abspath(__file__))
engine = None
try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 140)
except Exception:
    pass

def speak(msg):
    if engine:
        try:
            engine.say(msg)
            engine.runAndWait()
        except Exception:
            print(msg)
    else:
        print(msg)

def get_image():
    if USE_DEVICE_CAMERA:
        paths = capture_from_device(2, 0.3)
        if not paths:
            return None
        img = cv2.imread(paths[0])
        for p in paths:
            try:
                os.remove(p)
            except Exception:
                pass
        return img
    try:
        r = requests.get(CAMERA_URL, timeout=10)
        if r.status_code == 200:
            arr = np.frombuffer(r.content, np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print("Camera error:", e)
    return None

def main():
    speak("Currency detection starting. Loading YOLO 11.")
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Install: pip install ultralytics")
        speak("Please install ultralytics.")
        return
    # نموذج عملات مخصص إن وُجد، وإلا YOLO11 عام
    custom = os.path.join(script_dir, "weights", "currency_yolo11.pt")
    if os.path.isfile(custom):
        model = YOLO(custom)
    else:
        model = YOLO("yolo11n.pt")
    img = get_image()
    if img is None:
        speak("Could not capture image.")
        return
    results = model(img, conf=0.4, verbose=False)
    names = model.names
    detections = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = names.get(cls_id, f"class_{cls_id}")
            detections.append((label, conf))
    if not detections:
        speak("No currency or object detected.")
    else:
        # لو النموذج مخصص للعملات ستكون الأسماء من البيانات المدربة
        top = detections[0][0]
        speak(f"Detected: {top}")
        print("Detections:", detections)
    cv2.imshow("Currency YOLOv11", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
