# -*- coding: utf-8 -*-
"""
تقدير العمق - Depth-Anything-V2 | دقة التفاصيل المتناهية
متكيف مع CODE-M: مصدر الكاميرا من config.
"""
import os
import cv2
import numpy as np
import requests
from config import USE_DEVICE_CAMERA, CAMERA_URL, capture_from_device

# صوت
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
        paths = capture_from_device(1, 0.2)
        if not paths:
            return None
        img = cv2.imread(paths[0])
        try:
            os.remove(paths[0])
        except Exception:
            pass
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img is not None else None
    try:
        r = requests.get(CAMERA_URL, timeout=10)
        if r.status_code == 200:
            arr = np.frombuffer(r.content, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img is not None else None
    except Exception as e:
        print("Camera error:", e)
    return None

def main():
    speak("Depth estimation starting. Loading model.")
    try:
        from transformers import pipeline
        from PIL import Image
    except ImportError:
        print("Install: pip install transformers torch pillow")
        speak("Please install transformers and torch.")
        return
    try:
        pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
    except Exception as e:
        print("Model load error:", e)
        speak("Could not load depth model.")
        return
    img_rgb = get_image()
    if img_rgb is None:
        speak("Could not capture image.")
        return
    pil_img = Image.fromarray(img_rgb)
    depth = pipe(pil_img)["depth"]
    depth_np = np.array(depth)
    depth_np = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min() + 1e-8)
    depth_vis = (depth_np * 255).astype(np.uint8)
    depth_colormap = cv2.applyColorMap(depth_vis, cv2.COLORMAP_INFERNO)
    mean_depth = float(np.mean(depth_np))
    if mean_depth < 0.3:
        msg = "Objects appear close."
    elif mean_depth > 0.7:
        msg = "Scene is mostly far."
    else:
        msg = "Mixed depth. Moderate distance."
    speak(msg)
    cv2.imshow("Depth (Depth-Anything-V2)", depth_colormap)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
