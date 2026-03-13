# -*- coding: utf-8 -*-
"""
تمييز الوجوه - InsightFace | أعلى دقة "بصمة وجه" عالمياً
تسجيل وجه جديد: التقاط صور ثم حفظ التمثيل (embedding).
متكيف مع CODE-M: مصدر الكاميرا من config.
"""
import os
import cv2
import numpy as np
import requests
import pickle
from config import USE_DEVICE_CAMERA, CAMERA_URL, capture_from_device

script_dir = os.path.dirname(os.path.abspath(__file__))
registerd_dir = os.path.join(script_dir, "registerd")
os.makedirs(registerd_dir, exist_ok=True)

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

def get_images(count=6):
    if USE_DEVICE_CAMERA:
        paths = capture_from_device(count, 0.4)
        return [cv2.imread(p) for p in paths], paths
    imgs = []
    for _ in range(count):
        try:
            r = requests.get(CAMERA_URL, timeout=10)
            if r.status_code == 200:
                arr = np.frombuffer(r.content, np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if img is not None:
                    imgs.append(img)
        except Exception:
            pass
    return imgs, []

def main():
    speak("Face registration with InsightFace. Loading model.")
    try:
        from insightface.app import FaceAnalysis
    except ImportError:
        print("Install: pip install insightface onnxruntime")
        speak("Please install insightface.")
        return
    try:
        app = FaceAnalysis(name="buffalo_l", root=script_dir)
        app.prepare(ctx_id=0, det_size=(640, 640))
    except Exception as e:
        print("InsightFace load error:", e)
        speak("Could not load face model.")
        return
    # اسم جديد: آخر رقم في registerd + 1
    dirs = [0]
    for x in os.listdir(registerd_dir):
        try:
            dirs.append(int(x))
        except ValueError:
            continue
    new_id = str(max(dirs) + 1)
    save_dir = os.path.join(registerd_dir, new_id)
    os.makedirs(save_dir, exist_ok=True)
    speak("Capturing face images.")
    imgs, temp_paths = get_images(6)
    for p in temp_paths:
        try:
            os.remove(p)
        except Exception:
            pass
    if not imgs:
        speak("No images captured.")
        return
    embeddings_list = []
    for i, img in enumerate(imgs):
        faces = app.get(img)
        if faces:
            emb = faces[0].embedding
            embeddings_list.append(emb)
            cv2.imwrite(os.path.join(save_dir, f"image{i}.jpg"), img)
    if not embeddings_list:
        speak("No face detected in images.")
        return
    mean_embedding = np.mean(embeddings_list, axis=0).astype(np.float32)
    with open(os.path.join(save_dir, "embedding.pkl"), "wb") as f:
        pickle.dump(mean_embedding, f)
    speak("Face registered successfully with InsightFace.")
    print("Saved to", save_dir)

if __name__ == "__main__":
    main()
