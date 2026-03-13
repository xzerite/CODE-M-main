# -*- coding: utf-8 -*-
"""
وصف الصور - BLIP-2 | الفهم اللغوي العميق للصورة
متكيف مع CODE-M: مصدر الكاميرا من config.
"""
import os
import cv2
import numpy as np
import requests
from config import USE_DEVICE_CAMERA, CAMERA_URL, capture_from_device

engine = None
try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 130)
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
    speak("Image caption starting. Loading BLIP 2 model.")
    try:
        from transformers import Blip2Processor, Blip2ForConditionalGeneration
        import torch
    except ImportError:
        print("Install: pip install transformers torch")
        speak("Please install transformers and torch.")
        return
    try:
        processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
        model = Blip2ForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b")
    except Exception as e:
        print("Model load error:", e)
        speak("Could not load BLIP 2 model.")
        return
    img = get_image()
    if img is None:
        speak("Could not capture image.")
        return
    from PIL import Image
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    inputs = processor(images=pil_img, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=30)
    caption = processor.decode(out[0], skip_special_tokens=True).strip()
    if not caption:
        caption = "No caption generated."
    print("Caption:", caption)
    speak("Image shows: " + caption)
    cv2.putText(img, caption[:80], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.imshow("BLIP-2 Caption", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
