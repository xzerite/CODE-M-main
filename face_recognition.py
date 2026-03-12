import cv2
import face_recognition
import glob
import os
from config import CAMERA_URL
import matplotlib.pyplot as plt
import shutil
import pyaudio
import wave
import requests

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

AI_speak("face recognition has been activated")

# ======================================================================

directory = "unknowen"
parent_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(parent_dir, directory)
os.makedirs(path, exist_ok=True)
url = CAMERA_URL
for i in range(3):
    # التقاط صورة من ESP32
    response = requests.get(url)
    if response.status_code == 200:
        filename = f"{path}/image{i}.jpg"
        with open(filename, 'wb') as file:
            file.write(response.content)
        print(f"تم التقاط الصورة رقم {i+1} بنجاح!")
    else:
        print(f"فشل في التقاط الصورة رقم {i+1}.")

    if i == 2:
        # حذف أول صورة
        first_image_path = f"{path}/image0.jpg"
        os.remove(first_image_path)
        print("first picture is delete")    
# ============================================================================
known_faces = []
known_names = []
known_faces_paths = []

registerd_faces_paths = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registerd", "")
os.makedirs(registerd_faces_paths, exist_ok=True)

for name in os.listdir(registerd_faces_paths):
    images_mask = '%s%s/*.jpg' % (registerd_faces_paths, name)
    images_pathes = glob.glob(images_mask)
    known_faces_paths += images_pathes
    known_names += [name for x in images_pathes]

def get_encoding(img_path):
    image = face_recognition.load_image_file(img_path)
    encoding = face_recognition.face_encodings(image)
    return encoding[0]

known_faces = [get_encoding(img_path) for img_path in known_faces_paths]
unknown_image = glob.glob(os.path.join(path, '*.jpg'))
found_faces = []

for img_path in unknown_image:
    img = plt.imread(img_path)
    plt.figure()
    plt.imshow(img)
    encodings = face_recognition.face_encodings(img)
    found_faces = []
    for face_code in encodings:
        results = face_recognition.compare_faces(known_faces, face_code, tolerance=0.6)
        if any(results):
            found_faces.append(known_names[results.index(True)])
        elif any(results) == False:
            found_faces.append('unknowen')

if found_faces == []:
    found_faces.append('Unknown')

for i in found_faces:
    if i == 'Unknown':
        AI_speak("ًThis person is unknown")

    else:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Namesinvoice", "")
        filename = os.path.join(output_dir, f'{i}.wav')
        audio_file = wave.open(filename, "rb")
        audio = pyaudio.PyAudio()

        # Open the audio stream
        stream = audio.open(format=audio.get_format_from_width(audio_file.getsampwidth()),
                            channels=audio_file.getnchannels(),
                            rate=audio_file.getframerate(),
                            output=True)
        data = audio_file.readframes(1024)

        while data:
            stream.write(data)
            data = audio_file.readframes(1024)
        stream.stop_stream()
        stream.close()
        audio.terminate()

shutil.rmtree(path, ignore_errors=True)
cv2.destroyAllWindows()







# import cv2
# import face_recognition
# import glob
# import os
# import pyttsx3
# import matplotlib.pyplot as plt
# import shutil
# import pyaudio
# import wave


# def SpeakText(command):
#     engine = pyttsx3.init()
#     engine.say(command)
#     engine.runAndWait()


# SpeakText('face recognition mode on')

# directory = "unknowen"
# parent_dir = (f"C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project")
# path = os.path.join(parent_dir, directory)
# os.mkdir(path)
# cam = cv2.VideoCapture(0)
# cv2.waitKey(1000)
# for i in range(2):
#     cv2.waitKey(2000)
#     result, image = cam.read()
#     cv2.imshow("image", image)
#     cv2.imwrite(f"%s\image.jpg{i}.jpg" % (path), image)
#     i = i + 1
#     cv2.destroyWindow("image")

# known_faces = []
# known_names = []
# known_faces_paths = []
# # registerd_faces_paths = 'registerd/'
# registerd_faces_paths = "C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project\\registerd\\"

# for name in os.listdir(registerd_faces_paths):
#     images_mask = '%s%s/*.jpg' % (registerd_faces_paths, name)
#     images_pathes = glob.glob(images_mask)
#     known_faces_paths += images_pathes
#     known_names += [name for x in images_pathes]


# def get_encoding(img_path):
#     image = face_recognition.load_image_file(img_path)
#     encoding = face_recognition.face_encodings(image)
#     return encoding[0]


# known_faces = [get_encoding(img_path) for img_path in known_faces_paths]
# unknown_image = glob.glob('unknowen/*.jpg')
# found_faces = []
# for img_path in unknown_image:
#     img = plt.imread(img_path)
#     plt.figure()
#     plt.imshow(img)
#     encodings = face_recognition.face_encodings(img)
#     found_faces = []
#     for face_code in encodings:
#         results = face_recognition.compare_faces(known_faces, face_code, tolerance=0.6)
#         if any(results):
#             found_faces.append(known_names[results.index(True)])

#         elif any(results) == False:
#             found_faces.append('unknowen')


# if found_faces == []:
#     found_faces.append('Unknown')

# for i in found_faces:
#     if i == 'Unknown':
#         SpeakText('This person is unknown')

#     else:
#         output_dir ='C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project\\Namesinvoice\\'
#         filename = os.path.join(output_dir, f'{i}.wav')
#         audio_file = wave.open(filename, "rb")
#         audio = pyaudio.PyAudio()

#         # Open the audio stream
#         stream = audio.open(format=audio.get_format_from_width(audio_file.getsampwidth()),
#                             channels=audio_file.getnchannels(),
#                             rate=audio_file.getframerate(),
#                             output=True)
#         data = audio_file.readframes(1024)

#         while data:
#             stream.write(data)
#             data = audio_file.readframes(1024)
#         stream.stop_stream()
#         stream.close()
#         audio.terminate()

# shutil.rmtree(path, ignore_errors=True)
# cam.release()
# cv2.destroyAllWindows()
