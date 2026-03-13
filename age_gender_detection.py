import cv2
import math
import time
import requests
import os
import sys
import struct
import socket
import numpy as np
from config import STREAM_URL, USE_DEVICE_CAMERA

# ======================================================================
engine = None
try:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    voice_index = 1 if len(voices) > 1 else 0
    engine.setProperty('voice', voices[voice_index].id)
    engine.setProperty("rate", 145)
except Exception:
    pass

def AI_speak(something):
    if engine:
        try:
            engine.say(something)
            engine.runAndWait()
        except Exception:
            print(something)
    else:
        print(something)

# ======================================================================

def get_face_box(net, frame, conf_threshold=0.7):
    """كشف الوجه بنموذج TensorFlow DNN (opencv_face_detector_uint8.pb)."""
    frame_opencv_dnn = frame.copy()
    frame_height = frame_opencv_dnn.shape[0]
    frame_width = frame_opencv_dnn.shape[1]
    blob = cv2.dnn.blobFromImage(frame_opencv_dnn, 1.0, (300, 300), [104, 117, 123], True, False)
    net.setInput(blob)
    detections = net.forward()
    bboxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frame_width)
            y1 = int(detections[0, 0, i, 4] * frame_height)
            x2 = int(detections[0, 0, i, 5] * frame_width)
            y2 = int(detections[0, 0, i, 6] * frame_height)
            bboxes.append([x1, y1, x2, y2])
            cv2.rectangle(frame_opencv_dnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frame_height / 150)), 8)
    return frame_opencv_dnn, bboxes


def get_face_box_caffe(net, frame, conf_threshold=0.5):
    """كشف الوجه بنموذج Caffe SSD (face_deploy + face_net.caffemodel)."""
    frame_out = frame.copy()
    h, w = frame.shape[0], frame.shape[1]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], False, False)
    net.setInput(blob)
    try:
        out = net.forward()
    except Exception:
        return frame_out, []
    # Caffe SSD: [1, 1, N, 7] -> [batch, class, conf, xmin, ymin, xmax, ymax]
    if out.ndim != 4 or out.shape[2] == 0:
        return frame_out, []
    bboxes = []
    for i in range(out.shape[2]):
        conf = float(out[0, 0, i, 2])
        if conf < conf_threshold:
            continue
        x1 = int(out[0, 0, i, 3] * w)
        y1 = int(out[0, 0, i, 4] * h)
        x2 = int(out[0, 0, i, 5] * w)
        y2 = int(out[0, 0, i, 6] * h)
        x1, x2 = max(0, min(x1, x2)), min(w, max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(h, max(y1, y2))
        if x2 - x1 < 20 or y2 - y1 < 20:
            continue
        bboxes.append([x1, y1, x2, y2])
        cv2.rectangle(frame_out, (x1, y1), (x2, y2), (0, 255, 0), 2, 8)
    return frame_out, bboxes

# ======================================================================

# مسار مجلد الأوزان
script_dir = os.path.dirname(os.path.abspath(__file__))
weights_dir = os.path.join(script_dir, "weights")
os.makedirs(weights_dir, exist_ok=True)

FACE_PROTO = os.path.join(weights_dir, "opencv_face_detector.pbtxt")
FACE_MODEL = os.path.join(weights_dir, "opencv_face_detector_uint8.pb")
# نموذج الوجه Caffe (بديل عند غياب .pb)
FACE_CAFFE_PROTO = os.path.join(weights_dir, "face_deploy.prototxt")
FACE_CAFFE_MODEL = os.path.join(weights_dir, "face_net.caffemodel")
AGE_PROTO = os.path.join(weights_dir, "age_deploy.prototxt")
AGE_MODEL = os.path.join(weights_dir, "age_net.caffemodel")
GENDER_PROTO = os.path.join(weights_dir, "gender_deploy.prototxt")
GENDER_MODEL = os.path.join(weights_dir, "gender_net.caffemodel")

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
AGE_LIST = ["(0-2)", "(4-6)", "(8-12)", "(15-20)", "(25-32)", "(38-43)", "(48-53)", "(60-100)"]
GENDER_LIST = ["Male", "Female"]

# تحميل نموذج الوجه تلقائياً إن كان مفقوداً
def _download_face_model():
    if os.path.isfile(FACE_MODEL):
        return True
    urls = [
        "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20180220_uint8/opencv_face_detector_uint8.pb",
        "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20180220_uint8/opencv_face_detector_uint8.pb",
    ]
    for url in urls:
        try:
            print("Downloading opencv_face_detector_uint8.pb ...")
            r = requests.get(url, timeout=60, stream=True)
            r.raise_for_status()
            with open(FACE_MODEL, "wb") as f:
                for chunk in r.iter_content(chunk_size=32768):
                    f.write(chunk)
            print("Downloaded successfully.")
            return True
        except Exception as e:
            print(f"Try failed: {e}")
    return False

# كاشف وجه احتياطي (Haar) إذا فشل تحميل النموذج DNN
_face_cascade = None

def _init_face_cascade():
    global _face_cascade
    if _face_cascade is not None:
        return _face_cascade if _face_cascade is not False else None
    try:
        path = getattr(cv2.data, "haarcascades", None)
        if path:
            path = os.path.join(path, "haarcascade_frontalface_default.xml")
        if not path or not os.path.isfile(path):
            path = os.path.join(os.path.dirname(cv2.__file__), "data", "haarcascade_frontalface_default.xml")
        if os.path.isfile(path):
            _face_cascade = cv2.CascadeClassifier(path)
            if _face_cascade.empty():
                _face_cascade = False
        else:
            _face_cascade = False
    except Exception:
        _face_cascade = False
    return _face_cascade if _face_cascade is not False else None

def get_face_box_haar(frame, conf_threshold=0.7):
    """كشف الوجه بـ Haar cascade كبديل عند غياب النموذج DNN."""
    cascade = _init_face_cascade()
    if cascade is None or cascade is False:
        return frame, []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
    bboxes = []
    for (x, y, w, h) in faces:
        x1, y1, x2, y2 = x, y, x + w, y + h
        bboxes.append([x1, y1, x2, y2])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), int(round(frame.shape[0] / 150)), 8)
    return frame, bboxes

# Load models
face_net = None
face_net_caffe = None
age_net = None
gender_net = None

try:
    if not os.path.exists(FACE_MODEL):
        _download_face_model()
    if os.path.exists(FACE_MODEL) and os.path.exists(FACE_PROTO):
        face_net = cv2.dnn.readNet(FACE_MODEL, FACE_PROTO)
        print("Face detector: TensorFlow (.pb) loaded.")
    if face_net is None and os.path.exists(FACE_CAFFE_MODEL) and os.path.exists(FACE_CAFFE_PROTO):
        face_net_caffe = cv2.dnn.readNetFromCaffe(FACE_CAFFE_PROTO, FACE_CAFFE_MODEL)
        print("Face detector: Caffe (face_net) loaded.")
    if not all(os.path.exists(p) for p in (AGE_MODEL, GENDER_MODEL, AGE_PROTO, GENDER_PROTO)):
        raise FileNotFoundError("Missing age/gender weight files in 'weights/' folder.")
    age_net = cv2.dnn.readNet(AGE_MODEL, AGE_PROTO)
    gender_net = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)
    print("Age and gender models loaded.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    if face_net is None and face_net_caffe is None and _init_face_cascade():
        print("Using Haar cascade for face detection (fallback).")
    if age_net is None or gender_net is None:
        AI_speak("Model files are missing. Please check the weights folder.")
        face_net = face_net_caffe = age_net = gender_net = None

# ======================================================================

def run_live_age_gender():
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

    if USE_DEVICE_CAMERA:
        print("Using device camera (0)")
        cap = cv2.VideoCapture(0)
    else:
        stream_url = STREAM_URL
        cap = cv2.VideoCapture(stream_url)
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000000"

    AI_speak("Age and gender detection started.")
    last_speak_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            if USE_DEVICE_CAMERA:
                time.sleep(0.1)
                continue
            time.sleep(1)
            cap.open(STREAM_URL)
            continue

        def _process_faces(frame_face, bboxes):
            nonlocal last_speak_time
            out = frame_face
            for bbox in bboxes:
                y1 = max(0, bbox[1] - 20)
                y2 = min(frame.shape[0], bbox[3] + 20)
                x1 = max(0, bbox[0] - 20)
                x2 = min(frame.shape[1], bbox[2] + 20)
                face = frame[y1:y2, x1:x2]
                if face.size == 0 or face.shape[0] < 20 or face.shape[1] < 20:
                    continue
                try:
                    blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
                    gender_net.setInput(blob)
                    gender_preds = gender_net.forward()
                    gender = GENDER_LIST[gender_preds[0].argmax()]
                    age_net.setInput(blob)
                    age_preds = age_net.forward()
                    age = AGE_LIST[age_preds[0].argmax()]
                    label = f"{gender}, {age}"
                    cv2.putText(out, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
                    if time.time() - last_speak_time > 5:
                        AI_speak(f"Person detected. Looks like a {gender} aged {age}")
                        last_speak_time = time.time()
                except Exception:
                    pass
            return out

        if face_net is not None:
            frame_face, bboxes = get_face_box(face_net, frame)
            out_frame = _process_faces(frame_face, bboxes)
        elif face_net_caffe is not None:
            frame_face, bboxes = get_face_box_caffe(face_net_caffe, frame)
            out_frame = _process_faces(frame_face, bboxes)
        elif _init_face_cascade() and age_net is not None and gender_net is not None:
            frame_face, bboxes = get_face_box_haar(frame)
            out_frame = _process_faces(frame_face, bboxes)
        else:
            cv2.putText(frame, "MODELS MISSING", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            out_frame = frame

        if stream_sock:
            try:
                _, jpeg = cv2.imencode(".jpg", out_frame)
                stream_sock.sendall(struct.pack(">I", len(jpeg)) + jpeg.tobytes())
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
        else:
            cv2.imshow("Age and Gender Detection", out_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if stream_sock:
        try:
            stream_sock.close()
        except Exception:
            pass
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_live_age_gender()
