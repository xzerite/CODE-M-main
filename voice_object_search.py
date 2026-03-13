import cv2
import numpy as np
import speech_recognition as sr
import os
import requests
from config import CAMERA_URL, USE_DEVICE_CAMERA, capture_from_device

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

AI_speak("Search has been activated")

# ======================================================================

# ======================================================================

captured_files = []
if USE_DEVICE_CAMERA:
    import shutil
    raw = capture_from_device(2, 0.4)
    for i, p in enumerate(raw):
        filename = f'find_the_object_{i+1}.jpg'
        shutil.move(p, filename)
        captured_files.append(filename)
        print(f"Picture {i+1} has been successfully captured (device camera).")
else:
    url = CAMERA_URL
    for i in range(2):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                filename = f'find_the_object_{i+1}.jpg'
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

# ======================================================================



def takeCommand():
    r = sr.Recognizer()

    with sr.Microphone() as source:

        print("Listening...")
        AI_speak("Listening")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        print("Recognizing...")
        AI_speak("Recognizing")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")

    except Exception as e:
        print(e)
        print("Unable to Recognize your voice.")
        return "None"

    return query






def Camera(thing) :

     net = cv2.dnn.readNet('yolov3.weights', 'yolov3( find the object ).cfg')

     classes = []

     with open("coco.names", "r") as f:
         classes = f.read().splitlines()
         img = cv2.imread(r"find_the_object_2.jpg")

    # while True:
    # _, img = cap.read()
     height, width, _ = img.shape
     blob = cv2.dnn.blobFromImage(img, 1 / 255, (416, 416), (0, 0, 0), swapRB=True, crop=False)
     net.setInput(blob)
     output_layers_names = net.getUnconnectedOutLayersNames()
     layerOutputs = net.forward(output_layers_names)

     boxes = []
     confidences = []
     class_ids = []

     for output in layerOutputs:
         for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.2:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append((float(confidence)))
                class_ids.append(class_id)

     indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.2, 0.4)
     font = cv2.FONT_HERSHEY_PLAIN
     colors = np.random.uniform(0, 255, size=(100, 3))

     count_array=[]
     if len(indexes) > 0:
         for i in indexes.flatten():
             x, y, w, h = boxes[i]
             label = str(classes[class_ids[i]])
             confidence = str(round(confidences[i], 2))
             color = colors[i]
             cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
             cv2.putText(img, label + " " + confidence, (x, y + 20), font, 2, (255, 255, 255), 2)
         count_array.append(label)
         my_dict = {i: count_array.count(i) for i in count_array}
         if thing in my_dict:
             AI_speak('Yes')
         else:
             AI_speak("Nothing detected, please try again")


if __name__ == '__main__':
    clear = lambda: os.system('cls')

    clear()

    while True:
        query = takeCommand().lower()
        n = ''

        if 'start' in query:
            AI_speak("What are you searching for?")
            # n = takeCommand().lower()
            Camera(n)
            break