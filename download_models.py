# -*- coding: utf-8 -*-
"""
تحميل جميع النماذج مسبقاً لضمان عمل المودلات.
شغّل: python download_models.py
"""
import os
import sys

print("=" * 50)
print("تحميل النماذج - Downloading models...")
print("=" * 50)

# 1) Depth-Anything-V2
print("\n[1/3] Depth-Anything-V2 (تقدير العمق)...")
try:
    from transformers import pipeline
    pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
    print("   OK - Depth-Anything-V2")
except Exception as e:
    print("   خطأ:", e)
    print("   ثبّت: pip install transformers torch")

# 2) InsightFace
print("\n[2/3] InsightFace (تمييز الوجوه)...")
try:
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=0, det_size=(640, 640))
    print("   OK - InsightFace")
except Exception as e:
    print("   خطأ:", e)
    print("   ثبّت: pip install insightface onnxruntime")

# 3) YOLOv11
print("\n[3/3] YOLOv11 (كشف العملات)...")
try:
    from ultralytics import YOLO
    model = YOLO("yolo11n.pt")
    print("   OK - YOLOv11")
except Exception as e:
    print("   خطأ:", e)
    print("   ثبّت: pip install ultralytics")

print("\n" + "=" * 50)
print("انتهى التحميل.")
print("=" * 50)
