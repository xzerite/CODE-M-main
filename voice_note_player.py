from pydub import AudioSegment
from pydub.playback import play
import os
import wave
import pyaudio
import time
import signal
from inputimeout import inputimeout, TimeoutOccurred
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

AI_speak("voice note player has been activated")


# ========================================================================

def play_voice_note(directory):
    # إنشاء المجلد إن لم يكن موجوداً
    os.makedirs(directory, exist_ok=True)
    # Get all files in the directory
    files = os.listdir(directory)
    if len(files) > 0:
        # Sort the file names
        sorted_files = sorted(files)

        # Print the smallest and largest names
        smallest_name = sorted_files[0].split('.')[0]
        largest_name = sorted_files[-1].split('.')[0]
        print(f"Smallest name: {smallest_name}")
        print(f"Largest name: {largest_name}")
        x = f"Smallest name is: {smallest_name}"
        y = f" and the Largest name is: {largest_name}"
        z = x + y

        AI_speak(z)
        AI_speak("plase Enter the name of the voice note")





        # Get user input for the voice note name

        # note_name = input("Enter the name of the voice note: ")
        user_input = inputimeout(prompt="Enter the name of the voice note:", timeout=7)
        
          

        # Check if the voice note file exists
        file_path = os.path.join(directory, user_input + '.wav')
        print(f"File path: {file_path}")  # Debugging line
        if os.path.isfile(file_path):
            noteplayed= f"Voice note : {user_input } will be played ride now "
            AI_speak(noteplayed)


            audio_file = wave.open( file_path, "rb")
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
        else:
            print("Voice note not found!")
            notfound_message = f" Voice note{user_input} not found! it Seems to be out of the range "
            notfound_message2=  f"  try again but rememper that the range is from {smallest_name} to {largest_name} "

            
            AI_speak(notfound_message)
            AI_speak(notfound_message2)
            

    else:
        print("No voice notes found in the directory!")
        AI_speak("No voice notes found in the directory!")


# مجلد التسجيلات (بجانب السكربت) - نفس voice_note_recorder
directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records")

# Call the function to play the voice note and print smallest and largest names
play_voice_note(directory_path)
            
            


# import os
# import pyttsx3
# import wave
# import pyaudio
# import signal
# from pydub import AudioSegment
# from pydub.playback import play



# # ======================================================================

# voices = pyttsx3.init().getProperty('voices')
# voice_index = 1
# selected_voice = voices[voice_index].id
# engine = pyttsx3.init()
# engine.setProperty('voice', selected_voice)
# engine.setProperty("rate", 140)

# def AI_speak(something):
#     engine.say(something)
#     engine.runAndWait()

# AI_speak("ًvoice note player has been activated")

# # ======================================================================

# class TimeoutExpired(Exception):
#     pass

# def timeout_handler(signum, frame):
#     raise TimeoutExpired

# def input_with_timeout(prompt, timeout):
#     try:
#         signal.signal(signal.SIGALRM, timeout_handler)
#         signal.alarm(timeout)
#         return input(prompt)
#     except TimeoutExpired:
#         return None
#     finally:
#         signal.alarm(0)

# def play_voice_note(directory):
#     # Get all files in the directory
#     files = os.listdir(directory)
#     if len(files) > 0:
#         # Sort the file names
#         sorted_files = sorted(files)

#         # Print the smallest and largest names
#         smallest_name = sorted_files[0].split('.')[0]
#         largest_name = sorted_files[-1].split('.')[0]
#         print(f"Smallest name: {smallest_name}")
#         print(f"Largest name: {largest_name}")
#         x = f"Smallest name is: {smallest_name}"
#         y = f" and the Largest name is: {largest_name}"
#         z = x + y

#         AI_speak(z)

#         # Get user input for the voice note name with a timeout
#         note_name = input_with_timeout("Enter the name of the voice note (5 seconds timeout): ", 5)
#         if note_name is not None:
#             # Check if the voice note file exists
#             file_path = os.path.join(directory, note_name + '.wav')
#             print(f"File path: {file_path}")  # Debugging line
#             if os.path.isfile(file_path):
#                 note_played = f"Voice note : {note_name } will be played right now "
#                 AI_speak(note_played)

#                 audio_file = wave.open(file_path, "rb")
#                 audio = pyaudio.PyAudio()

#                 # Open the audio stream
#                 stream = audio.open(format=audio.get_format_from_width(audio_file.getsampwidth()),
#                                     channels=audio_file.getnchannels(),
#                                     rate=audio_file.getframerate(),
#                                     output=True)
#                 data = audio_file.readframes(1024)
                
#                 while data:
#                     stream.write(data)
#                     data = audio_file.readframes(1024)
                
#                 stream.stop_stream()
#                 stream.close()
#                 audio.terminate()
#             else:
#                 print("Voice note not found!")
#                 not_found_message = f" Voice note {note_name} not found! It seems to be out of the range."
#                 not_found_message2 = f" Try again, but remember that the range is from {smallest_name} to {largest_name}."

#                 AI_speak(not_found_message)
#                 AI_speak(not_found_message2)
#         else:
#             print("No input provided within the timeout!")
#             AI_speak("No input provided within the timeout!")
#     else:
#         print("No voice notes found in the directory!")
#         AI_speak("No voice notes found in the directory!")

# # Specify the directory where the voice notes are stored
# directory_path = "C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project\\records"

# # Call the function to play the voice note and print smallest and largest names
# play_voice_note(directory_path)
