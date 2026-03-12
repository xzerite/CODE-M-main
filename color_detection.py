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

def AI_speak(something):
    if engine:
        try:
            engine.say(something)
            engine.runAndWait()
        except Exception:
            print(something)
    else:
        print(something)
    return something

AI_speak("color detection has been activated")

# ======================================================================

# =====================================================================================
url = CAMERA_URL
captured_files = []

for i in range(2):  # Try capturing two images
    try:
        # Send GET request to capture the image
        response = requests.get(url, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Use relative filenames
            filename = f'Color_detection_{i+1}.jpg'
            with open(filename, 'wb') as file:
                file.write(response.content)
            captured_files.append(filename)
            print(f"Picture {i+1} has been successfully captured.")
        else:
            print(f"Failed to take the picture {i+1}. Status code: {response.status_code}")
            AI_speak(f"Failed to capture image {i+1} from camera.")
    except Exception as e:
        print(f"Error connecting to camera: {e}")
        AI_speak("Error connecting to camera.")

# If we failed to capture the second image, we cannot proceed
if len(captured_files) < 2:
    if len(captured_files) == 1:
        os.remove(captured_files[0]) # Cleanup
    print("Error: Could not capture images from camera. Please check the CAMERA_IP in config.py.")
    exit()

# Delete first picture (often used to clear buffer on some ESP32-CAM firmware)
if os.path.exists(captured_files[0]):
    os.remove(captured_files[0])
    print("First picture deleted (buffer cleared).")

#======================================================================================        

img = cv2.imread(captured_files[1])
if img is None:
    print(f"Error: Could not load image '{captured_files[1]}'.")
    exit()
# img.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
# img.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# while True:
#     _, frame = cap.read()
hsv_frame = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
height, width, _ = img.shape

cx = int(width / 2)
cy = int(height / 2)

# Pick pixel value
pixel_center = hsv_frame[cy, cx]
hue_value = pixel_center[0]
saturation = pixel_center[1]
value = pixel_center[2]



color = "Undefined"
if saturation < 20:
        if value > 200:
            color = AI_speak("White")
        else:
            color = AI_speak("White")
elif hue_value < 5 or hue_value > 175:
        color = AI_speak("Red")
elif hue_value < 22:
        color = AI_speak("Orange")
elif hue_value < 33:
        color = AI_speak("Yellow")
elif hue_value < 78:
        color = AI_speak("Green")
elif hue_value < 130:
        color = AI_speak("Black")
elif hue_value < 170:
        color = AI_speak("Magenta")
else:
        color = "Purple"

# Check for pink
if color == "Magenta" and value > 200:
        color = AI_speak("Pink")
        
# Check for maroon
if color == "Red" and value < 50:
        color =AI_speak("Maroon")

# Check for brown
if color == "Orange" and value < 100:
        color = AI_speak("brown")

pixel_center_bgr = img[cy, cx]
b, g, r = int(pixel_center_bgr[0]), int(pixel_center_bgr[1]), int(pixel_center_bgr[2])
cv2.putText(img, color, (10, 50), 5, 3, (b, g, r), 4)
cv2.circle(img, (cx, cy), 25, (255, 0, 0), 5)
if(color == "Undefined") is True:
        AI_speak("Magenta")

    


cv2.imshow('Image', img)
cv2.destroyAllWindows()
cv2.waitKey(0)
