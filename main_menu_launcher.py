import subprocess
import os
import time
# ======================================================================

# تجربة تحميل الصوت (قد يفشل على بعض أجهزة الماك)
# Try loading text-to-speech (may fail on some Macs)
engine = None
try:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    voice_index = 1 if len(voices) > 1 else 0
    engine.setProperty('voice', voices[voice_index].id)
    engine.setProperty("rate", 140)
except Exception:
    print("الصوت غير متاح - Voice unavailable (البرنامج يعمل بدون نطق)")

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




while True:

    user_input = input()

    if user_input == "0":
        subprocess.run(["python", "0.py"])
    elif user_input == "1":
        subprocess.run(["python", "1.py"])
    elif user_input == "2":
        subprocess.run(["python", "voice_object_search.py"])
    elif user_input == "3":
        subprocess.run(["python", "object_distance_calculator.py"])
    elif user_input == "4":
        subprocess.run(["python", "text_recognition_ocr.py"])
    elif user_input == "5":
        subprocess.run(["python", "register_new_face.py"])
    elif user_input == "6":
        subprocess.run(["python", "face_recognition.py"])
    elif user_input == "7":
        subprocess.run(["python", "7.py"])
    elif user_input == "8":
        subprocess.run(["python", "8.py"])
    elif user_input == "9":
        subprocess.run(["python", "currency_recognition.py"])
    elif user_input == "10":
        subprocess.run(["python", "image_caption_generator.py"])
    elif user_input == "11":
        subprocess.run(["python", "voice_note_recorder.py"])
    elif user_input == "12":
        subprocess.run(["python", "voice_note_player.py"])
    elif user_input == "13":
        subprocess.run(["python", "age_gender_detection.py"])
    elif user_input == "14":
        subprocess.run(["python", "color_detection.py"])
    elif user_input == "15":
        subprocess.run(["python", "traffic_sign_detection.py"])
    elif user_input == "16":
        subprocess.run(["python", "16.py"])
    elif user_input == "17":
        subprocess.run(["python", "17.py"])
    elif user_input == "18":
        subprocess.run(["python", "18.py"])
    elif user_input == "19":
        subprocess.run(["python", "19.py"])
    
    else:
        AI_speak("Invalid input. Please enter either from 0 to 16 without 10.")
        print("Invalid input. Please enter either from 1 to 16 without 10.")
