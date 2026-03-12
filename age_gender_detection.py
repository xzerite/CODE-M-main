import argparse
import cv2
import math
import sys
import os
import requests
from config import CAMERA_URL

# ======================================================================
engine = None
try:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    voice_index = 1 if len(voices) > 1 else 0
    engine.setProperty('voice', voices[voice_index].id)
    engine.setProperty("rate", 140)
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

AI_speak("age and gender detection has been activated")

# ======================================================================

def highlightFace(net, frame, conf_threshold=0.7):
  frameOpencvDnn=frame.copy()
  frameHeight=frameOpencvDnn.shape[0]
  frameWidth=frameOpencvDnn.shape[1]
  blob=cv2.dnn.blobFromImage(frameOpencvDnn,1.0,(300,300),[104,117,123],
                             True,False)
  net.setInput(blob)
  detections=net.forward()
  faceBoxes=[]
  for i in range(detections.shape[2]):
    confidence=detections[0,0,i,2]
    if confidence>conf_threshold:
      x1 = int(detections[0, 0, i, 3] * frameWidth)
      y1 = int(detections[0, 0, i, 4] * frameHeight)
      x2 = int(detections[0, 0, i, 5] * frameWidth)
      y2 = int(detections[0, 0, i, 6] * frameHeight)
      faceBoxes.append([x1,y1,x2,y2])
      cv2.rectangle(frameOpencvDnn, (x1,y1), (x2,y2), (0,255,0),
                    int(round(frameHeight/150)),8)
  return frameOpencvDnn,faceBoxes

parser= argparse.ArgumentParser()
parser.add_argument('--image')

args = parser.parse_args()

# مسار مجلد الأوزان (بجانب السكربت)
_weights_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")

# Defined the model files
FACE_PROTO = os.path.join(_weights_dir, "opencv_face_detector.pbtxt")
FACE_MODEL = os.path.join(_weights_dir, "opencv_face_detector_uint8.pb")
AGE_PROTO = os.path.join(_weights_dir, "age_deploy.prototxt")
AGE_MODEL = os.path.join(_weights_dir, "age_net.caffemodel")
GENDER_PROTO = os.path.join(_weights_dir, "gender_deploy.prototxt")
GENDER_MODEL = os.path.join(_weights_dir, "gender_net.caffemodel")

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
AGE_LIST = ["(0-2)", "(4-6)", "(8-12)", "(15-20)", "(25-32)", "(38-43)", "(48-53)", "(60-100)"]
GENDER_LIST = ["Male", "Female"]

# Load network (يحتاج ملفات الأوزان في مجلد weights/)
if not os.path.isfile(FACE_MODEL):
    print("ضع ملفات الأوزان في مجلد weights/ (انظر INSTALL.md أو README)")
    sys.exit(1)
FACE_NET = cv2.dnn.readNet(FACE_MODEL, FACE_PROTO)
AGE_NET = cv2.dnn.readNet(AGE_MODEL, AGE_PROTO)
GENDER_NET = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)


# video= cv2.VideoCapture(0) # use default camera
# box_padding = 20
# hasFrame, frame= video.read()
# if not hasFrame:
#   print("Error: Could not read frame from camera")
#   sys.exit(1)

# =====================================================================================
url = CAMERA_URL
captured_files = []

for i in range(2):  # Try capturing two images
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filename = f'age_gender_{i+1}.jpg'
            with open(filename, 'wb') as file:
                file.write(response.content)
            captured_files.append(filename)
            print(f"Picture {i+1} has been successfully captured.")
        else:
            print(f"Failed to take the picture {i+1}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error connecting to camera: {e}")

if len(captured_files) < 2:
    if len(captured_files) == 1:
        os.remove(captured_files[0])
    print("Error: Could not capture images from camera.")
    AI_speak("Error capturing images from camera.")
    sys.exit(1)

# Delete first picture (buffer clearing)
if os.path.exists(captured_files[0]):
    os.remove(captured_files[0])
    print("First picture deleted.")

#======================================================================================

image_path = captured_files[1]
box_padding = 20

frame = cv2.imread(image_path)
if frame is None:
    print(f"Error: Could not read image from {image_path}")
    sys.exit(1)

resultImg,faceBoxes= highlightFace(FACE_NET,frame)
if not faceBoxes:
  print("No face detected")
  AI_speak("No face detected")

else:
  for faceBox in faceBoxes:
    face= frame[max(0, faceBox[1]-box_padding):
                min(faceBox[3]+box_padding,frame.shape[0]-1),max(0,faceBox[0]-box_padding)
               :min(faceBox[2]+box_padding,frame.shape[1]-1)]

    blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
    GENDER_NET.setInput(blob)
    gender_predictions = GENDER_NET.forward()
    gender = GENDER_LIST[gender_predictions[0].argmax()]
    print(f"Gender: {gender}")

    AGE_NET.setInput(blob)
    age_predictions = AGE_NET.forward()
    age = AGE_LIST[age_predictions[0].argmax()]
    print(f"Age:{age[1:-1]} years")


    cv2.putText(resultImg, f'{gender}, {age}', (faceBox[0], faceBox[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
    gender_age_str = f"Gender: {gender}, Age: {age[1:-1]} years"
    AI_speak(gender_age_str)
    # cv2.imshow('Detecting age and gender', resultImg)
