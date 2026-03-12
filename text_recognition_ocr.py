import cv2
from PIL import Image
from pytesseract import pytesseract
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

AI_speak("text recognition has been activated")

# ======================================================================


# =====================================================================================
url = CAMERA_URL
for i in range(2):  # تكرار العملية مرة لالتقاط صورتين
    # إرسال طلب GET لالتقاط الصورة
    response = requests.get(url)

    # التحقق من نجاح الطلب
    if response.status_code == 200:
        # حفظ الصورة الملتقطة
        filename = f'C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project\\text_recognition_{i+1}.jpg'
        with open(filename, 'wb') as file:
            file.write(response.content)
        print(f"picture {i+1} has been successfully")

        # # عرض الصورة الملتقطة باستخدام OpenCV
        # image = cv2.imread(filename)
        # cv2.imshow(f'Captured Image {i+1}', image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
    else:
        print(f"Failed to take the picture {i+1} ")

   
# حذف أول صورة
first_image_path = f"text_recognition_1.jpg"
os.remove(first_image_path)
print("first picture is delete") 
                

#======================================================================================  




def tesseract():
 img = cv2.imread(r'C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project\\text_recognition_2.jpg')

 path_to_tesseract = r"c:\\Program Files\\Tesseract-OCR\\tesseract.exe"
 pytesseract.tesseract_cmd = path_to_tesseract
 text = pytesseract.image_to_string(Image.fromarray(img))
 AI_speak(text)
 #-------------------------------
 i=0
 for n in text:
     if(n =="\n" or n==" "):
         continue
     else:
         i=i+1

 if(i<1):
     AI_speak("nothing detected, please try again")

tesseract()


