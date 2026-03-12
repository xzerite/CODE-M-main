import sounddevice as sd
import soundfile as sf
import os

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

AI_speak("voice note recorder has been activated")

# ======================================================================

def record_voice(directory):
    # إنشاء المجلد إن لم يكن موجوداً | Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    # Check if the directory is empty
    if not os.listdir(directory):
        record_name = '1'
        max_record_name = 0
    else:
        # Get the largest record name so far
        existing_records = [int(f.split('.')[0]) for f in os.listdir(directory) if f.endswith('.wav')]
        max_record_name = max(existing_records) if existing_records else 0
        record_name = str(max_record_name + 1)

    x = f"the last record name is : {max_record_name}"
    
    AI_speak(x)
    AI_speak("record will be start ride now and for 1 minute")

    # Set the recording duration in seconds
    duration = 60

    # Record audio (mono=1 يعمل على الماك ومعظم المايكات | works on Mac and most mics)
    recording = sd.rec(int(duration * 44100), samplerate=44100, channels=1)

    # Wait for the recording to finish
    sd.wait()

    # Save the recording to the specified directory
    file_path = os.path.join(directory, record_name + '.wav')
    sf.write(file_path, recording, 44100, 'PCM_24')

    print(f"Successfully saved the recording to the file: {file_path}")
    x=f"recording has been ended and saved with the  name: {record_name}"
    AI_speak(x)


# مجلد التسجيلات (بجانب ملف السكربت) يعمل على ويندوز وماك
# Records folder (next to script) - works on Windows and Mac
directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records")

# Call the function to record the voice
record_voice(directory_path)
