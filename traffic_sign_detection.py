import cv2
import requests
import os
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

def AI_speak(label):
    AI_speak.has_been_called = True
    if engine:
        try:
            engine.say(label)
            engine.runAndWait()
        except Exception:
            print(label)
    else:
        print(label)

AI_speak.has_been_called = False
if engine:
    try:
        engine.say("traffic sign detection has been activated")
        engine.runAndWait()
    except Exception:
        print("traffic sign detection has been activated")
else:
    print("traffic sign detection has been activated")

# ===========================================================================================

url = CAMERA_URL
captured_files = []

for i in range(2):  # Try capturing two images
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filename = f'trafficsign_detection_{i+1}.jpg'
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
    exit()

# Delete first picture (buffer clearing)
if os.path.exists(captured_files[0]):
    os.remove(captured_files[0])
    print("First picture deleted.")

# ===========================================================================================
# Stop Sign Cascade Classifier xml
yieldsign = cv2.CascadeClassifier('yieldsign12Stages.xml')
Traffic_Light = cv2.CascadeClassifier('TrafficLight_HAAR_16Stages.xml')
stop_sign = cv2.CascadeClassifier('cascade_stop_sign.xml')
Speedlimit = cv2.CascadeClassifier('Speedlimit_24_15Stages.xml')

img = cv2.imread(captured_files[1])
if img is None:
    print(f"Error: Could not load image '{captured_files[1]}'.")
    exit()

# while cap.isOpened():
#   _, img = cap.read()
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
yieldsign_scaled = yieldsign.detectMultiScale(gray, 1.3, 5)
Traffic_Light_scaled = Traffic_Light.detectMultiScale(gray, 1.3, 5)
stop_sign_scaled = stop_sign.detectMultiScale(gray, 1.3, 5)
Speedlimit_scaled = Speedlimit.detectMultiScale(gray, 1.3, 5)
    
# Detect the stop sign, x,y = origin points, w = width, h = height
for (x, y, w, h) in stop_sign_scaled:
        # Draw rectangle around the stop sign
    stop_sign_rectangle = cv2.rectangle(img, (x,y),(x+w, y+h), (0, 255, 0), 3)
        # Write "Stop sign" on the bottom of the rectangle
    stop_sign_text = cv2.putText(img=stop_sign_rectangle,
                                     text=AI_speak("Stop Sign"),
                                     org=(x, y+h+30),
                                     fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                     fontScale=1, color=(0, 0, 255),
                                     thickness=2, lineType=cv2.LINE_4)

    # Detect the Yield Sign, x,y = origin points, w = width, h = height
for (x, y, w, h) in yieldsign_scaled:
        # Draw rectangle around the stop sign
        yieldsign_rectangle = cv2.rectangle(img, (x,y),
                                            (x+w, y+h),
                                            (0, 255, 0), 3)
        # Write "Yield Sign" on the bottom of the rectangle
        yieldsign_text = cv2.putText(img=yieldsign_rectangle,
                                     text=AI_speak("Yield Sign Stop"),
                                     org=(x, y+h+30),
                                     fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                     fontScale=1, color=(0, 0, 255),
                                     thickness=2, lineType=cv2.LINE_4)
                                     
for (x, y, w, h) in Traffic_Light_scaled:
        # Draw rectangle around the stop sign
        Traffic_Light_rectangle = cv2.rectangle(img, (x,y),
                                            (x+w, y+h),
                                            (0, 255, 0), 3)
        # Write "Traffic Light Red Stop" on the bottom of the rectangle
        Traffic_Light_text = cv2.putText(img=Traffic_Light_rectangle,
                                     text=AI_speak("Traffic Light Red Stop"),
                                     org=(x, y+h+30),
                                     fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                     fontScale=1, color=(0, 0, 255),
                                     thickness=2, lineType=cv2.LINE_4)
                                     
    # Detect the Speedlimit, x,y = origin points, w = width, h = height
for (x, y, w, h) in Speedlimit_scaled:
        # Draw rectangle around the stop sign
        Speedlimit_rectangle = cv2.rectangle(img, (x,y),
                                            (x+w, y+h),
                                            (0, 255, 0), 3)
        # Write "Speedlimit" on the bottom of the rectangle
        Speedlimit_text = cv2.putText(img=Speedlimit_rectangle,
                                     text=AI_speak("Speedlimit Sign"),
                                     org=(x, y+h+30),
                                     fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                     fontScale=1, color=(0, 0, 255),
                                     thickness=2, lineType=cv2.LINE_4)

if(AI_speak.has_been_called):
    pass
else:
    AI_speak("nothing detected, please try again ")
# cv2.imshow("img", img)
# cv2.destroyAllWindows()

