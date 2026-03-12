import cv2
import os
import glob as gb
import sounddevice as sd
import wavio
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

AI_speak("add new face has been activated")

# ======================================================================
_script_dir = os.path.dirname(os.path.abspath(__file__))
path_of_name = os.path.join(_script_dir, "registerd")
os.makedirs(path_of_name, exist_ok=True)

dirnames = [0]
for folder in os.listdir(path_of_name): 
    folder = int(folder)
    dirnames.append(folder)
 
new_name=max(dirnames)
new_name=int(new_name)+1
new_name=str(new_name)
 


AI_speak("ًwhat is the person name")


duration = 5
sample_rate = 44100
channels = 1   # mono يعمل على الماك ومعظم المايكات
output_dir = os.path.join(_script_dir, "Namesinvoice")
os.makedirs(output_dir, exist_ok=True)   

print('Recording started. Speak now...')
recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
sd.wait()   

filename = os.path.join(output_dir,f'{new_name}.wav')
wavio.write(filename, recording, sample_rate, sampwidth=2)

print('Audio recorded and saved to', filename)
AI_speak("ًsaved person name has been success")


# ==========================================================================
directory = new_name
parent_dir = path_of_name
path = os.path.join(parent_dir, directory)
os.makedirs(path, exist_ok=True)

url = CAMERA_URL
captured_count = 0

for i in range(6): # Try to take 6 pictures
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filename = os.path.join(path, f"image{i}.jpg")
            with open(filename, 'wb') as file:
                file.write(response.content)
            print(f"Picture {i+1} has been successfully captured.")
            captured_count += 1
        else:
            print(f"Failed to take picture {i+1}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error capturing picture {i+1}: {e}")

if captured_count == 0:
    print("Error: Could not capture any images for registration.")
    AI_speak("Error capturing images.")
    # Cleanup empty directory
    os.rmdir(path)
    exit()

# If we captured at least one image, we can consider it a success
# (Though the first image is often skipped to clear buffer)
first_img = os.path.join(path, "image0.jpg")
if os.path.exists(first_img) and captured_count > 1:
    os.remove(first_img)
    print("First picture deleted (buffer cleared).")

AI_speak("Saved person face successfully.")
cv2.destroyAllWindows()



