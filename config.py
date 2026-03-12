# ============================================================
# إعدادات الكاميرا - Camera settings
# ============================================================
# غيّر عنوان IP هنا فقط، وكل الملفات ستستخدمه تلقائياً
# Change the IP address here only; all scripts will use it
# ============================================================

# عنوان IP لكاميرا ESP32-CAM (بدون http)
# IP address of ESP32-CAM (without http://)
# عنوان IP لكاميرا ESP32-CAM (بدون http)
# IP address of ESP32-CAM (without http://)
CAMERA_IP = "192.168.8.12"

# المسار الافتراضي للحصول على صورة - Default path for capture
# تم التأكد أن "/capture" هو المسار الصحيح لهذة الكاميرا
# Verified that "/capture" is the correct path for this camera
CAMERA_URL_PATH = "/capture" 

# روابط جاهزة (لا تغيّر إلا لو الكاميرا تستخدم مسار مختلف)
CAMERA_URL = f"http://{CAMERA_IP}{CAMERA_URL_PATH}"
CAMERA_URL_240 = f"http://{CAMERA_IP}/240x240.jpg"
