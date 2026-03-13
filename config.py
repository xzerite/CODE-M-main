# ============================================================
# إعدادات الكاميرا - Camera settings
# ============================================================
# غيّر عنوان IP هنا أو من الواجهة (متغير البيئة CAMERA_IP)
# Change the IP here or from the launcher UI (env CAMERA_IP)
# ============================================================

import os

# عنوان IP لكاميرا ESP32-CAM (بدون http) - يُؤخذ من الواجهة إن وُجد
# IP address of ESP32-CAM (without http://) - from launcher UI if set
CAMERA_IP = os.environ.get("CAMERA_IP", "192.168.8.12")

# استخدام كاميرا الجهاز (1) أو بث IP (0) - من الواجهة
# Use device camera (1) or IP stream (0) - set from launcher UI
USE_DEVICE_CAMERA = os.environ.get("USE_DEVICE_CAMERA", "0") == "1"


def capture_from_device(num_frames=1, delay=0.3):
    """التقاط إطار/إطارات من كاميرا الجهاز (0). يُرجع قائمة مسارات ملفات صور."""
    import cv2
    import tempfile
    import time
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return []
    paths = []
    try:
        for i in range(num_frames):
            ret, frame = cap.read()
            if not ret:
                break
            if i > 0:
                time.sleep(delay)
            fd, path = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)
            cv2.imwrite(path, frame)
            paths.append(path)
    finally:
        cap.release()
    return paths

# المسار الافتراضي للحصول على صورة - Default path for capture
# تم التأكد أن "/capture" هو المسار الصحيح لهذة الكاميرا
# Verified that "/capture" is the correct path for this camera
CAMERA_URL_PATH = "/capture" 

# روابط جاهزة (لا تغيّر إلا لو الكاميرا تستخدم مسار مختلف)
CAMERA_URL = f"http://{CAMERA_IP}{CAMERA_URL_PATH}"
CAMERA_URL_240 = f"http://{CAMERA_IP}/240x240.jpg"
STREAM_URL = f"http://{CAMERA_IP}:81/stream"
