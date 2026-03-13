import cv2
from PIL import Image
from pytesseract import pytesseract
import requests
import os
import time
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

AI_speak("text recognition has been activated")

# ======================================================================


# =====================================================================================
captured_files = []
if USE_DEVICE_CAMERA:
    captured_files = capture_from_device(2, 0.5)
    for i in range(len(captured_files)):
        print(f"Picture {i+1} has been successfully captured (device camera).")
else:
    url = CAMERA_URL
    for i in range(2):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                filename = f'text_recognition_{i+1}.jpg'
                with open(filename, 'wb') as file:
                    file.write(response.content)
                captured_files.append(filename)
                print(f"Picture {i+1} has been successfully captured.")
            else:
                print(f"Failed to take the picture {i+1}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error connecting to camera for picture {i+1}: {e}")
        if i < 1:
            time.sleep(2)

if not captured_files:
    AI_speak("Error: Could not capture any images from camera.")
    print("Error: Could not capture images from camera.")
    exit()

# Use the last captured image
img_to_use = captured_files[-1]
print(f"Using {img_to_use} for recognition.")

# Cleanup other captured files
for f in captured_files:
    if f != img_to_use and os.path.exists(f):
        os.remove(f)
        print(f"Cleaned up temporary file: {f}")

#======================================================================================  

def tesseract():
    img = cv2.imread(img_to_use)
    if img is None:
        print(f"Error: Could not load image '{img_to_use}'.")
        return

    path_to_tesseract = r"c:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    pytesseract.tesseract_cmd = path_to_tesseract
    try:
        text = pytesseract.image_to_string(Image.fromarray(img))
        AI_speak(text)
        
        # Count non-whitespace characters
        char_count = sum(1 for n in text if n not in ["\n", " "])
        if char_count < 1:
            AI_speak("nothing detected, please try again")
    except Exception as e:
        print(f"Tesseract error: {e}")
        AI_speak("Error during text recognition.")

tesseract()


