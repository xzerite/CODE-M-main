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

# منفذ ومسار البث (من الواجهة). فارغ = البث على الرابط الرئيسي /
CAMERA_STREAM_PORT = os.environ.get("CAMERA_STREAM_PORT", "80")
_path = (os.environ.get("CAMERA_STREAM_PATH") or "").strip().strip("/")

# روابط جاهزة
CAMERA_URL = f"http://{CAMERA_IP}{CAMERA_URL_PATH}"
CAMERA_URL_240 = f"http://{CAMERA_IP}/240x240.jpg"
# رابط البث: إذا المسار فارغ -> http://IP:80/ وإلا -> http://IP:80/stream
STREAM_URL = f"http://{CAMERA_IP}:{CAMERA_STREAM_PORT}/" + (_path if _path else "")
# روابط بديلة للمحاولة لو الرابط الرئيسي فشل
STREAM_URL_ALTERNATIVES = [
    f"http://{CAMERA_IP}:{CAMERA_STREAM_PORT}/",
    f"http://{CAMERA_IP}:{CAMERA_STREAM_PORT}/video",
    f"http://{CAMERA_IP}:{CAMERA_STREAM_PORT}/live.flv",
    f"http://{CAMERA_IP}:{CAMERA_STREAM_PORT}/stream",
    f"http://{CAMERA_IP}:{CAMERA_STREAM_PORT}/mjpeg",
    f"http://{CAMERA_IP}:80/",
    f"http://{CAMERA_IP}:80/video",
    f"http://{CAMERA_IP}:80/live.flv",
    f"http://{CAMERA_IP}:80/stream",
    f"http://{CAMERA_IP}:80/mjpeg",
    f"http://{CAMERA_IP}/",
    f"http://{CAMERA_IP}/video",
    f"http://{CAMERA_IP}/live.flv",
    f"http://{CAMERA_IP}/stream",
]


# ========== حل بديل: بث MJPEG عبر HTTP (بدون FFmpeg) ==========
class MJPEGHTTPCapture:
    """قارئ بث MJPEG عبر HTTP — يعمل عندما يفشل OpenCV/FFmpeg. واجهة مشابهة لـ VideoCapture."""

    def __init__(self, url, timeout=10):
        import threading
        import requests
        self._url = url
        self._timeout = timeout
        self._latest = None
        self._lock = threading.Lock()
        self._closed = False
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()
        # انتظار أول إطار (حتى ~12 ثانية — ESP32 قد يكون بطيئاً)
        for _ in range(120):
            if self._closed:
                break
            with self._lock:
                if self._latest is not None:
                    break
            import time
            time.sleep(0.1)

    def _stream_loop(self):
        import requests
        import cv2
        import numpy as np
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0", "Accept": "multipart/x-mixed-replace, */*"}
            r = requests.get(self._url, stream=True, timeout=max(self._timeout, 15), headers=headers)
            r.raise_for_status()
            buf = b""
            for chunk in r.iter_content(chunk_size=16384):
                if self._closed:
                    break
                buf += chunk
                # ESP32 قد يرسل رؤوس multipart قبل كل إطار — نبحث عن بداية JPEG
                a = buf.find(b"\xff\xd8")
                if a != -1:
                    b = buf.find(b"\xff\xd9", a)
                    if b != -1 and b > a:
                        jpg = buf[a : b + 2]
                        buf = buf[b + 2 :]
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            with self._lock:
                                self._latest = frame
        except Exception:
            pass
        self._closed = True

    def isOpened(self):
        return not self._closed

    def read(self):
        import copy
        with self._lock:
            if self._latest is not None:
                return True, self._latest.copy()
        return False, None

    def release(self):
        self._closed = True


# ========== طريقة بديلة: بث من صور متتالية (استعلام /capture) ==========
class SnapshotPollCapture:
    """بث من صور متتالية: طلب متكرر لرابط التقاط صورة واحدة (مثل /capture في ESP32-CAM). واجهة مشابهة لـ VideoCapture."""

    def __init__(self, url, interval=0.25):
        import threading
        import requests
        import time
        import cv2
        import numpy as np
        self._url = url.rstrip("/")
        if "/capture" not in self._url:
            self._url = self._url.rstrip("/") + "/capture"
        self._interval = interval
        self._latest = None
        self._lock = threading.Lock()
        self._closed = False
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        for _ in range(40):
            if self._closed:
                break
            with self._lock:
                if self._latest is not None:
                    break
            time.sleep(0.1)

    def _poll_loop(self):
        import requests
        import time
        import cv2
        import numpy as np
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"}
        while not self._closed:
            try:
                r = requests.get(self._url, timeout=5, headers=headers)
                r.raise_for_status()
                arr = np.frombuffer(r.content, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is not None:
                    with self._lock:
                        self._latest = frame
            except Exception:
                pass
            time.sleep(self._interval)

    def isOpened(self):
        return not self._closed

    def read(self):
        with self._lock:
            if self._latest is not None:
                return True, self._latest.copy()
        return False, None

    def release(self):
        self._closed = True


def _try_snapshot_poll(base_url):
    """تجربة البث عبر استعلام متكرر لـ /capture. يُرجع SnapshotPollCapture أو None."""
    try:
        base = base_url.rstrip("/")
        for suf in ("/stream", "/video", "/mjpeg", "/live.flv"):
            if base.endswith(suf):
                base = base[: -len(suf)]
                break
        capture_url = base.rstrip("/") + "/capture"
        cap = SnapshotPollCapture(capture_url, interval=0.2)
        if cap.read()[0]:
            return cap
        cap.release()
    except Exception:
        pass
    return None


def _try_mjpeg_http(url, timeout=8):
    """تجربة فتح بث MJPEG عبر HTTP (بدون FFmpeg). يُرجع MJPEGHTTPCapture أو None."""
    try:
        cap = MJPEGHTTPCapture(url, timeout=timeout)
        if cap.read()[0]:
            return cap
        cap.release()
    except Exception:
        pass
    return None


def open_stream_capture():
    """فتح بث الكاميرا: أولاً OpenCV/FFmpeg، ثم إن فشل نجرّب قارئ MJPEG عبر HTTP. أو MJPEG فقط إن USE_MJPEG_HTTP=1."""
    import cv2
    use_mjpeg_only = os.environ.get("USE_MJPEG_HTTP", "").strip() == "1"
    urls = [STREAM_URL] + [u for u in STREAM_URL_ALTERNATIVES if u != STREAM_URL]
    if use_mjpeg_only:
        for url in urls:
            cap = _try_mjpeg_http(url)
            if cap is not None:
                print("Stream OK (MJPEG HTTP):", url)
                return cap
        for url in urls:
            cap = _try_snapshot_poll(url)
            if cap is not None:
                print("Stream OK (Snapshot /capture):", url)
                return cap
        return None
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;10000000"
    for url in urls:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print("Stream OK (FFmpeg):", url)
                return cap
        try:
            cap.release()
        except Exception:
            pass
    for url in urls:
        cap = _try_mjpeg_http(url)
        if cap is not None:
            print("Stream OK (MJPEG HTTP):", url)
            return cap
    for url in urls:
        cap = _try_snapshot_poll(url)
        if cap is not None:
            print("Stream OK (Snapshot /capture):", url)
            return cap
    cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
    return cap if cap.isOpened() else None
