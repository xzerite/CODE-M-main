# -*- coding: utf-8 -*-
"""
واجهة تشغيل المودلات مع إدخال IP الكاميرا
Launcher UI: enter camera IP, choose model, run. Video stream in browser.
"""
import os
import subprocess
import socket
import struct
import threading
import time
from pathlib import Path

from flask import Flask, render_template_string, request, jsonify, Response

app = Flask(__name__)

# مجلد المشروع (لتشغيل السكربتات منه)
PROJECT_DIR = Path(__file__).resolve().parent

# مودلات تعرض البث داخل المتصفح (بدل نافذة OpenCV)
STREAMABLE_MODELS = ["color_detection.py", "traffic_light_recognition.py", "face_analysis.py", "text_recognition.py"]

# بث المودل: آخر إطار + قفل + العملية الحالية
_stream_frame = None
_stream_lock = threading.Lock()
_stream_process = None
_stream_listener_socket = None

# قائمة المودلات المتاحة (اسم العرض => اسم الملف)
MODELS = [
    ("كشف الألوان - Color Detection", "color_detection.py"),
    ("تحليل الوجه (عمر، جنس، انفعال) - Face Analysis", "face_analysis.py"),
    ("التعرف على الوجه - Face Recognition", "face_recognition.py"),
    ("إشارة المرور الضوئية - Traffic Light", "traffic_light_recognition.py"),
    ("قراءة النص OCR - Text Recognition", "text_recognition.py"),
    ("تقدير العمق - Depth-Anything-V2", "depth_estimation.py"),
    ("البحث الصوتي - Voice Object Search", "voice_object_search.py"),
    ("تمييز الوجوه - InsightFace", "face_insight.py"),
    ("كشف العملات - YOLOv11", "currency_yolo11.py"),
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تشغيل المودلات - CODE-M</title>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f1419;
            --card: #1a2332;
            --accent: #1d9bf0;
            --accent-hover: #1a8cd8;
            --text: #e7e9ea;
            --muted: #71767b;
            --border: #2f3336;
            --success: #00ba7c;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'IBM Plex Sans Arabic', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
        }
        .container {
            max-width: 720px;
            margin: 0 auto;
        }
        h1 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .sub {
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 2rem;
        }
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }
        input[type="text"] {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--bg);
            color: var(--text);
            font-size: 1rem;
            font-family: inherit;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: var(--accent);
        }
        input::placeholder {
            color: var(--muted);
        }
        select {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--bg);
            color: var(--text);
            font-size: 1rem;
            font-family: inherit;
            cursor: pointer;
        }
        select:focus {
            outline: none;
            border-color: var(--accent);
        }
        .field { margin-bottom: 1.25rem; }
        .field:last-child { margin-bottom: 0; }
        .btn {
            width: 100%;
            padding: 0.9rem 1.5rem;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-run {
            background: var(--accent);
            color: white;
            margin-top: 0.5rem;
        }
        .btn-run:hover {
            background: var(--accent-hover);
        }
        .btn-run:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .msg {
            margin-top: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 10px;
            font-size: 0.9rem;
            display: none;
        }
        .msg.show { display: block; }
        .msg.success { background: rgba(0,186,124,0.2); color: var(--success); }
        .msg.error { background: rgba(244,33,46,0.2); color: #f4212e; }
        .radio-group { display: flex; gap: 1rem; flex-wrap: wrap; }
        .radio-label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            font-weight: 400;
        }
        .radio-label input { width: auto; }
        #videoCard { margin-top: 1rem; width: 100%; }
        #videoCard h3 { font-size: 1rem; margin-bottom: 0.5rem; }
        .video-wrap {
            background: #000;
            border-radius: 12px;
            overflow: hidden;
            aspect-ratio: 4/3;
            width: 100%;
            min-height: 360px;
            max-height: 70vh;
        }
        .video-wrap img { width: 100%; height: 100%; object-fit: contain; display: block; min-height: 320px; }
        .btn-stop { background: #e74c3c; margin-top: 0.5rem; }
        .btn-stop:hover { background: #c0392b; }
        .btn-check { background: #3498db; font-size: 0.9rem; }
        .btn-check:hover { background: #2980b9; }
        .btn-check:disabled { opacity: 0.7; cursor: wait; }
    </style>
</head>
<body>
    <div class="container">
        <h1>تشغيل المودلات</h1>
        <p class="sub">اختر المودل وأدخل IP الكاميرا ثم اضغط تشغيل</p>

        <div class="card" id="videoCard" style="display: none;">
            <h3>بث المودل</h3>
            <div class="video-wrap">
                <img id="streamImg" src="" alt="البث المباشر">
            </div>
            <button type="button" class="btn btn-run btn-stop" id="btnStop">إيقاف المودل</button>
        </div>

        <div class="card">
            <form id="form">
                <div class="field">
                    <label>مصدر الكاميرا</label>
                    <div class="radio-group">
                        <label class="radio-label">
                            <input type="radio" name="source" value="stream" checked>
                            <span>بث (IP الكاميرا)</span>
                        </label>
                        <label class="radio-label">
                            <input type="radio" name="source" value="device">
                            <span>كاميرا الجهاز</span>
                        </label>
                    </div>
                </div>
                <div class="field" id="ipField">
                    <label for="ip">IP الكاميرا <span class="sub" style="font-weight: normal;">(نوع: ESP32-CAM)</span></label>
                    <input type="text" id="ip" name="ip" placeholder="مثال: 192.168.8.12" value="192.168.8.12" autocomplete="off">
                </div>
                <div class="field" id="streamOpts">
                    <label for="streamPort">منفذ البث</label>
                    <input type="text" id="streamPort" name="streamPort" placeholder="80" value="80" style="width: 5rem;">
                    <label for="streamPathSelect" style="margin-top: 0.5rem;">مسار البث (اختر من القائمة)</label>
                    <select id="streamPathSelect" name="streamPath" style="max-width: 12rem;">
                        <option value="">/ (فارغ)</option>
                        <option value="video">video</option>
                        <option value="live.flv">live.flv</option>
                        <option value="stream" selected>stream</option>
                        <option value="mjpeg">mjpeg</option>
                        <option value="__other__">أخرى (أدخل أدناه)</option>
                    </select>
                    <input type="text" id="streamPathCustom" name="streamPathCustom" placeholder="مثلاً capture أو custom" style="max-width: 10rem; margin-top: 0.25rem; display: none;">
                    <p class="sub" style="margin-top: 0.5rem; font-size: 0.8rem;">من تطبيق البث: انسخ عنوان LAN (مثلاً <code>192.168.1.3:80</code> أو <code>192.168.1.3:8081</code>) وضع الـ IP في الحقل أعلاه والمنفذ في «منفذ البث». تأكد أن خادم البث يعمل في التطبيق (ليس «RTSP Server Closed»—فعّل بث HTTP أو Live Push إن وُجد).</p>
                    <p class="sub" style="margin-top: 0.25rem; font-size: 0.8rem;">ESP32-CAM: من Arduino انسخ عنوان البث من الشاشة التسلسلية (مثلاً :80/stream أو :81/stream). مسار البث الشائع: <code>stream</code>.</p>
                    <p class="sub" style="margin-top: 0.25rem; font-size: 0.8rem;">لرفع الدقة والإطارات (s60sc / MJPEG2SD): ضع <code>config.txt</code> على الـ SD أو استخدم واجهة الويب على <code>http://IP_الكاميرا</code>. مثلاً: <code>framesize 11</code> (HD)، <code>streamdelay 0</code> أو أقل = إطارات أكثر.</p>
                    <label class="sub" style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; font-size: 0.85rem;">
                        <input type="checkbox" id="useMjpegHttp" name="useMjpegHttp" value="1">
                        استخدام طرق بديلة فقط (MJPEG عبر HTTP ثم التقاط صور /capture)
                    </label>
                    <button type="button" class="btn btn-check" id="btnCheckIp" style="margin-top: 0.5rem;">تأكد أن IP الكاميرا شغال</button>
                    <button type="button" class="btn btn-check" id="btnCheckStream" style="margin-top: 0.35rem;">تحقق اتصال من البث</button>
                    <button type="button" class="btn btn-check" id="btnTestAllPaths" style="margin-top: 0.35rem;">اختبار كل المسارات واختيار المتصل</button>
                </div>
                <div class="field">
                    <label for="model">المودل</label>
                    <select id="model" name="model">
                        {% for label, script in models %}
                        <option value="{{ script }}">{{ label }}</option>
                        {% endfor %}
                    </select>
                </div>
                <button type="submit" class="btn btn-run" id="btnRun">تشغيل</button>
            </form>
            <div id="msg" class="msg"></div>
        </div>
    </div>
    <script>
        const form = document.getElementById('form');
        const msg = document.getElementById('msg');
        const btnRun = document.getElementById('btnRun');

        function showMsg(text, isError) {
            msg.textContent = text;
            msg.className = 'msg show ' + (isError ? 'error' : 'success');
        }

        const sourceStream = document.querySelector('input[name="source"][value="stream"]');
        const ipField = document.getElementById('ipField');
        const streamOpts = document.getElementById('streamOpts');
        sourceStream.addEventListener('change', () => { ipField.style.display = 'block'; streamOpts.style.display = 'block'; });
        document.querySelector('input[name="source"][value="device"]').addEventListener('change', () => { ipField.style.display = 'none'; streamOpts.style.display = 'none'; });

        document.getElementById('streamPathSelect').addEventListener('change', function() {
            document.getElementById('streamPathCustom').style.display = this.value === '__other__' ? 'block' : 'none';
        });

        function getStreamPath() {
            const sel = document.getElementById('streamPathSelect');
            if (sel.value === '__other__') return (document.getElementById('streamPathCustom').value || '').trim();
            return (sel.value || '').trim();
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
                const source = document.querySelector('input[name="source"]:checked').value;
            const ip = document.getElementById('ip').value.trim();
            const streamPort = document.getElementById('streamPort').value.trim() || '80';
            const streamPath = getStreamPath();
            const model = document.getElementById('model').value;
            if (source === 'stream' && !ip) {
                showMsg('أدخل IP الكاميرا عند اختيار البث', true);
                return;
            }
            btnRun.disabled = true;
            try {
                const r = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip, model, source, streamPort, streamPath, useMjpegHttp: document.getElementById('useMjpegHttp').checked })
                });
                const data = await r.json();
                if (data.ok) {
                    if (data.streamable) {
                        document.getElementById('videoCard').style.display = 'block';
                        document.getElementById('streamImg').src = '/video_feed?t=' + Date.now();
                        showMsg('يعمل المودل. الشاشة تظهر أعلاه. اضغط إيقاف لإغلاقه.');
                    } else {
                        showMsg('تم تشغيل المودل. ستظهر نافذة البرنامج. أغلقها عند الانتهاء.');
                    }
                } else {
                    showMsg(data.error || 'حدث خطأ', true);
                }
            } catch (err) {
                showMsg('خطأ في الاتصال: ' + err.message, true);
            }
            btnRun.disabled = false;
        });

        document.getElementById('btnStop').addEventListener('click', async () => {
            try {
                await fetch('/stop', { method: 'POST' });
                document.getElementById('videoCard').style.display = 'none';
                document.getElementById('streamImg').src = '';
                showMsg('تم إيقاف المودل.');
            } catch (e) { showMsg('خطأ في الإيقاف', true); }
        });

        document.getElementById('btnCheckIp').addEventListener('click', async () => {
            const ip = document.getElementById('ip').value.trim();
            const streamPort = document.getElementById('streamPort').value.trim() || '80';
            if (!ip) {
                showMsg('أدخل IP الكاميرا أولاً', true);
                return;
            }
            const btn = document.getElementById('btnCheckIp');
            btn.disabled = true;
            showMsg('جاري التحقق من وصول الكاميرا...', false);
            try {
                const r = await fetch('/check_ip', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip, streamPort })
                });
                const data = await r.json();
                if (data.ok) {
                    showMsg(data.message || 'IP الكاميرا يعمل ✓', false);
                } else {
                    showMsg(data.error || 'لا يمكن الوصول إلى الكاميرا', true);
                }
            } catch (err) {
                showMsg('خطأ: ' + err.message, true);
            }
            btn.disabled = false;
        });

        document.getElementById('btnCheckStream').addEventListener('click', async () => {
            const ip = document.getElementById('ip').value.trim();
            const streamPort = document.getElementById('streamPort').value.trim() || '80';
            const streamPath = getStreamPath();
            if (!ip) {
                showMsg('أدخل IP الكاميرا أولاً', true);
                return;
            }
            const btn = document.getElementById('btnCheckStream');
            btn.disabled = true;
            showMsg('جاري التحقق من الاتصال...', false);
            try {
                const r = await fetch('/check_stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip, streamPort, streamPath })
                });
                const data = await r.json();
                if (data.ok) {
                    showMsg('اتصال ناجح بالبث: ' + (data.url || ''), false);
                } else {
                    showMsg(data.error || 'فشل الاتصال بالبث', true);
                }
            } catch (err) {
                showMsg('خطأ: ' + err.message, true);
            }
            btn.disabled = false;
        });

        document.getElementById('btnTestAllPaths').addEventListener('click', async () => {
            const ip = document.getElementById('ip').value.trim();
            const streamPort = document.getElementById('streamPort').value.trim() || '80';
            if (!ip) {
                showMsg('أدخل IP الكاميرا أولاً', true);
                return;
            }
            const btn = document.getElementById('btnTestAllPaths');
            btn.disabled = true;
            showMsg('جاري اختبار كل المسارات...', false);
            try {
                const r = await fetch('/test_all_paths', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip, streamPort })
                });
                const data = await r.json();
                if (data.ok) {
                    const path = data.path || '';
                    const sel = document.getElementById('streamPathSelect');
                    const custom = document.getElementById('streamPathCustom');
                    if (path === '' || path === 'video' || path === 'live.flv' || path === 'stream' || path === 'mjpeg') {
                        sel.value = path;
                        custom.style.display = 'none';
                    } else {
                        sel.value = '__other__';
                        custom.value = path;
                        custom.style.display = 'block';
                    }
                    showMsg('تم اختيار المسار المتصل: ' + (path || '/') + ' — ' + (data.url || ''), false);
                } else {
                    document.getElementById('useMjpegHttp').checked = true;
                    showMsg('الجهاز يستجيب لكن لم يُكتشف بث. تم تفعيل «طرق بديلة» — اضغط «تشغيل» (سيُجرّب MJPEG ثم /capture).', true);
                }
            } catch (err) {
                showMsg('خطأ: ' + err.message, true);
            }
            btn.disabled = false;
        });
    </script>
</body>
</html>
"""


def _stream_listener(port):
    """يستقبل إطارات JPEG من المودل ويخزن آخر إطار في _stream_frame."""
    global _stream_frame, _stream_listener_socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", port))
        sock.listen(1)
        _stream_listener_socket = sock
        conn, _ = sock.accept()
        try:
            while True:
                buf = conn.recv(4)
                if len(buf) < 4:
                    break
                n = struct.unpack(">I", buf)[0]
                data = b""
                while len(data) < n:
                    chunk = conn.recv(min(65536, n - len(data)))
                    if not chunk:
                        break
                    data += chunk
                if len(data) == n:
                    with _stream_lock:
                        _stream_frame = data
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            conn.close()
    except Exception:
        pass
    finally:
        with _stream_lock:
            _stream_frame = None
        try:
            sock.close()
        except Exception:
            pass
        _stream_listener_socket = None


def _placeholder_jpeg():
    """صورة placeholder عند انتظار البث."""
    try:
        from PIL import Image
        from io import BytesIO
        img = Image.new("RGB", (320, 240), (40, 40, 40))
        buf = BytesIO()
        img.save(buf, "JPEG", quality=85)
        return buf.getvalue()
    except Exception:
        pass
    # minimal 1x1 gray jpeg fallback if PIL missing
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07"
        b"\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d"
        b"\x1a\x1c\x1c $.\' \x1c\x1c(7),01444\x1f\'9=82<.ff\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03"
        b"\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfc\xbe\xff\xd9"
    )

_PLACEHOLDER_JPEG = _placeholder_jpeg()


def _gen_frames():
    """مولد بث MJPEG للإطار الحالي."""
    boundary = b"frame"
    while True:
        with _stream_lock:
            frame = _stream_frame
        if frame:
            yield b"--" + boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        else:
            yield b"--" + boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + _PLACEHOLDER_JPEG + b"\r\n"
        time.sleep(0.033)


@app.route("/video_feed")
def video_feed():
    return Response(
        _gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/stop", methods=["POST"])
def stop_stream():
    global _stream_process
    if _stream_process is not None:
        try:
            _stream_process.terminate()
            _stream_process.wait(timeout=3)
        except Exception:
            _stream_process.kill()
        _stream_process = None
    return jsonify(ok=True)


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, models=MODELS)


@app.route("/run", methods=["POST"])
def run():
    global _stream_process, _stream_frame
    try:
        data = request.get_json() or {}
        ip = (data.get("ip") or "").strip()
        script = (data.get("model") or "").strip()
        source = (data.get("source") or "stream").strip()
        use_device = source == "device"

        if not use_device and not ip:
            return jsonify(ok=False, error="IP الكاميرا مطلوب عند اختيار البث")
        if not script or not any(s == script for _, s in MODELS):
            return jsonify(ok=False, error="المودل غير صالح")

        script_path = PROJECT_DIR / script
        if not script_path.is_file():
            return jsonify(ok=False, error=f"الملف غير موجود: {script}")

        env = os.environ.copy()
        env["CAMERA_IP"] = ip
        env["USE_DEVICE_CAMERA"] = "1" if use_device else "0"
        if not use_device:
            env["CAMERA_STREAM_PORT"] = (data.get("streamPort") or "").strip() or "80"
            env["CAMERA_STREAM_PATH"] = (data.get("streamPath") or "").strip()
            if data.get("useMjpegHttp"):
                env["USE_MJPEG_HTTP"] = "1"

        streamable = script in STREAMABLE_MODELS
        if streamable:
            if _stream_process is not None:
                try:
                    _stream_process.terminate()
                    _stream_process.wait(timeout=2)
                except Exception:
                    _stream_process.kill()
                _stream_process = None
            with _stream_lock:
                _stream_frame = None
            port = 9765
            thread = threading.Thread(target=_stream_listener, args=(port,), daemon=True)
            thread.start()
            time.sleep(0.3)
            env["STREAM_TO_BROWSER"] = "1"
            env["STREAM_PORT"] = str(port)

        _stream_process = subprocess.Popen(
            ["python", str(script_path)],
            cwd=str(PROJECT_DIR),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return jsonify(ok=True, streamable=streamable)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


def _check_stream_connection(ip, port, path):
    """تجربة فتح بث الكاميرا بالـ IP والمنفذ والمسار المعطاة. يُرجع (success, url_or_error)."""
    import cv2
    port = (port or "80").strip() or "80"
    path = (path or "").strip().strip("/")
    base = f"http://{ip}:{port}/"
    stream_url = base + (path if path else "")
    alternatives = [
        base,
        f"http://{ip}:{port}/video",
        f"http://{ip}:{port}/live.flv",
        f"http://{ip}:{port}/stream",
        f"http://{ip}:{port}/mjpeg",
        f"http://{ip}:80/",
        f"http://{ip}:80/video",
        f"http://{ip}:80/live.flv",
        f"http://{ip}:80/stream",
        f"http://{ip}:80/mjpeg",
        "http://{}/".format(ip),
        "http://{}/video".format(ip),
        "http://{}/live.flv".format(ip),
        "http://{}/stream".format(ip),
    ]
    urls = [stream_url] + [u for u in alternatives if u != stream_url]
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;10000000"
    for url in urls:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            ret, _ = cap.read()
            try:
                cap.release()
            except Exception:
                pass
            if ret:
                return True, url
    # طريقة بديلة: MJPEG عبر HTTP
    for url in urls:
        ok, _ = _try_mjpeg_http_url(url, timeout=10)
        if ok:
            return True, url
    if not _can_reach_host(ip, port):
        return False, f"لا يمكن الوصول إلى {ip}:{port}. تأكد أن الكاميرا على نفس الشبكة والمنفذ صحيح."
    return False, "الجهاز يستجيب لكن لم يُكتشف بث. جرّب تفعيل «طرق بديلة فقط» ثم اضغط «تشغيل» (MJPEG أو /capture)."


def _can_reach_host(ip, port):
    """التحقق من إمكانية الوصول إلى الجهاز على المنفذ (اتصال TCP)."""
    try:
        port = int((port or "80").strip() or "80")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip.strip(), port))
        s.close()
        return True
    except Exception:
        return False


def _try_mjpeg_http_url(url, timeout=12):
    """تجربة فتح الرابط كبث MJPEG عبر HTTP (بدون FFmpeg). يُرجع (True, url) إن وُجد إطار JPEG أو بداية JPEG."""
    try:
        import requests
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0", "Accept": "multipart/x-mixed-replace, */*"}
        r = requests.get(url, stream=True, timeout=timeout, headers=headers)
        r.raise_for_status()
        buf = b""
        for i, chunk in enumerate(r.iter_content(chunk_size=16384)):
            if i > 200:
                break
            buf += chunk
            if len(buf) < 2:
                continue
            a = buf.find(b"\xff\xd8")
            if a != -1:
                b = buf.find(b"\xff\xd9", a)
                if b != -1 and b > a:
                    return True, url
                if len(buf) > 50000:
                    buf = buf[a:]
        return False, ""
    except Exception:
        return False, ""


def _test_all_paths(ip, port):
    """تجربة مسارات البث: أولاً OpenCV/FFmpeg، ثم الطريقة البديلة MJPEG عبر HTTP. يُرجع (success, path, url)."""
    import cv2
    port = (port or "80").strip() or "80"
    paths_to_try = ["", "video", "live.flv", "stream", "mjpeg"]
    base = f"http://{ip}:{port}/"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;10000000"
    for path in paths_to_try:
        url = base + (path.strip("/") if path else "")
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            ret, _ = cap.read()
            try:
                cap.release()
            except Exception:
                pass
            if ret:
                return True, path if path else "", url
    # طريقة بديلة: MJPEG عبر HTTP (بدون FFmpeg)
    for path in paths_to_try:
        url = base + (path.strip("/") if path else "")
        ok, u = _try_mjpeg_http_url(url)
        if ok:
            return True, path if path else "", u
    return False, "", ""


@app.route("/test_all_paths", methods=["POST"])
def test_all_paths():
    """اختبار كل المسارات وإرجاع أول مسار متصل."""
    try:
        data = request.get_json() or {}
        ip = (data.get("ip") or "").strip()
        if not ip:
            return jsonify(ok=False, error="IP الكاميرا مطلوب")
        port = (data.get("streamPort") or "").strip() or "80"
        ok, path, url = _test_all_paths(ip, port)
        if ok:
            return jsonify(ok=True, path=path, url=url)
        if not _can_reach_host(ip, port):
            err = f"لا يمكن الوصول إلى {ip}:{port}. تأكد أن الكاميرا ESP32 تعمل وعلى نفس شبكة الجهاز (Wi‑Fi)، وأن المنفذ صحيح."
        else:
            err = "الجهاز يستجيب لكن لم يُكتشف بث. فعّل «طرق بديلة فقط» واضغط «تشغيل» — سيُجرّب MJPEG ثم التقاط صور من /capture (مناسب لـ ESP32-CAM)."
        return jsonify(ok=False, error=err)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


@app.route("/check_ip", methods=["POST"])
def check_ip():
    """التحقق من إمكانية الوصول إلى IP الكاميرا والمنفذ (اتصال TCP فقط)."""
    try:
        data = request.get_json() or {}
        ip = (data.get("ip") or "").strip()
        if not ip:
            return jsonify(ok=False, error="أدخل IP الكاميرا أولاً.")
        port = (data.get("streamPort") or "").strip() or "80"
        if _can_reach_host(ip, port):
            return jsonify(ok=True, message=f"IP الكاميرا يعمل — تم الوصول إلى {ip}:{port}")
        return jsonify(ok=False, error=f"لا يمكن الوصول إلى {ip}:{port}. تأكد أن الكاميرا تعمل وعلى نفس الشبكة (Wi‑Fi) والمنفذ صحيح.")
    except Exception as e:
        return jsonify(ok=False, error=str(e))


@app.route("/check_stream", methods=["POST"])
def check_stream():
    """التحقق من إمكانية الاتصال ببث الكاميرا حسب IP ومنفذ ومسار من الطلب."""
    try:
        data = request.get_json() or {}
        ip = (data.get("ip") or "").strip()
        if not ip:
            return jsonify(ok=False, error="IP الكاميرا مطلوب")
        port = (data.get("streamPort") or "").strip() or "80"
        path = (data.get("streamPath") or "").strip()
        ok, result = _check_stream_connection(ip, port, path)
        if ok:
            return jsonify(ok=True, url=result)
        return jsonify(ok=False, error=result)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
  #yyy  