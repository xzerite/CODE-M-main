import cv2
import math
import time
import requests
import os
import sys
import numpy as np
from config import STREAM_URL

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

# ======================================================================

# مسار مجلد الأوزان
script_dir = os.path.dirname(os.path.abspath(__file__))
weights_dir = os.path.join(script_dir, "weights")

FACE_PROTO = os.path.join(weights_dir, "opencv_face_detector.pbtxt")
FACE_MODEL = os.path.join(weights_dir, "opencv_face_detector_uint8.pb")
AGE_PROTO = os.path.join(weights_dir, "age_deploy.prototxt")
AGE_MODEL = os.path.join(weights_dir, "age_net.caffemodel")
GENDER_PROTO = os.path.join(weights_dir, "gender_deploy.prototxt")
GENDER_MODEL = os.path.join(weights_dir, "gender_net.caffemodel")

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
AGE_LIST = ["(0-2)", "(4-6)", "(8-12)", "(15-20)", "(25-32)", "(38-43)", "(48-53)", "(60-100)"]
GENDER_LIST = ["Male", "Female"]

# Load models
try:
    if not os.path.exists(FACE_MODEL):
        raise FileNotFoundError("Missing weight files in 'weights/' folder.")
    
    face_net = cv2.dnn.readNet(FACE_MODEL, FACE_PROTO)
    age_net = cv2.dnn.readNet(AGE_MODEL, AGE_PROTO)
    gender_net = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)
except Exception as e:
    print(f"Error: {e}")
    print("Please ensure all model files are in the 'weights' folder.")
    AI_speak("Model files are missing. Please check the weights folder.")
    # Define dummy nets to avoid crash during window init if models missing
    face_net = age_net = gender_net = None

# ======================================================================

def run_live_age_gender():
    stream_url = STREAM_URL
    cap = cv2.VideoCapture(stream_url)
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000000"
    
    AI_speak("Age and gender detection started.")
    last_speak_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(1)
            cap.open(stream_url)
            continue

        if face_net:
            frame_face, bboxes = get_face_box(face_net, frame)
            for bbox in bboxes:
                face = frame[max(0, bbox[1]-20):min(bbox[3]+20, frame.shape[0]-1),
                             max(0, bbox[0]-20):min(bbox[2]+20, frame.shape[1]-1)]

                blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
                
                # Gender
                gender_net.setInput(blob)
                gender_preds = gender_net.forward()
                gender = GENDER_LIST[gender_preds[0].argmax()]
                
                # Age
                age_net.setInput(blob)
                age_preds = age_net.forward()
                age = AGE_LIST[age_preds[0].argmax()]

                label = f"{gender}, {age}"
                cv2.putText(frame_face, label, (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
                
                if time.time() - last_speak_time > 5:
                    AI_speak(f"Person detected. Looks like a {gender} aged {age}")
                    last_speak_time = time.time()
            
            cv2.imshow("Age and Gender Detection", frame_face)
        else:
            cv2.putText(frame, "MODELS MISSING", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Age and Gender Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_live_age_gender()
