import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style="whitegrid")
import os
import glob as gb
import cv2
import tensorflow as tf
import keras
import shutil
from collections import Counter
import requests
from config import CAMERA_URL_240, USE_DEVICE_CAMERA, capture_from_device

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

AI_speak("currency recognition has been activated")

# ======================================================================

directory = "predection"
parent_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(parent_dir, directory)

# Check if the directory already exists
if os.path.exists(path):
    shutil.rmtree(path)
os.makedirs(path, exist_ok=True)
# ======================================================================
captured_files = []
if USE_DEVICE_CAMERA:
    import shutil
    raw = capture_from_device(11, 0.3)
    for i, p in enumerate(raw):
        filename = os.path.join(path, f'mony_{i+1}.jpg')
        shutil.move(p, filename)
        captured_files.append(filename)
else:
    url = CAMERA_URL_240
    for i in range(11):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                filename = os.path.join(path, f'mony_{i+1}.jpg')
                with open(filename, 'wb') as file:
                    file.write(response.content)
                captured_files.append(filename)
                print(f"Picture {i+1} has been successfully captured.")
            else:
                print(f"Failed to take the picture {i+1}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error connecting to camera: {e}")

if not captured_files:
    print("Error: Could not capture any images from camera.")
    AI_speak("Error capturing images from camera.")
    exit()

# Delete first picture (buffer clearing)
if os.path.exists(captured_files[0]):
    os.remove(captured_files[0])
    print("First picture deleted.")

# ======================================================================

model_path = os.path.join(parent_dir, "model.h5")
if not os.path.exists(model_path):
    print(f"Error: Model file not found at {model_path}")
    exit()

model = tf.keras.models.load_model(model_path)
files = gb.glob(pathname=os.path.join(path, '*.jpg'))
print(f'For Prediction data , found {len(files)}')

if not files:
    print("Error: No captured images found in predection folder.")
    AI_speak("No images to analyze.")
    exit()

s = 400
X_pred = []
for file in files: 
    image = cv2.imread(file)
    image_array = cv2.resize(image , (s,s))
    X_pred.append(list(image_array)) 


print(f'we have {len(X_pred)} items in X_pred')

X_pred_array = np.array(X_pred)
y_result = model.predict(X_pred_array)
print('Prediction Shape is {}'.format(y_result.shape))

code = {'100 from f':0,'100 from b':1,'200 from b ':2,'200 from f ':3,'50 from b':4,'50 from f':5,
        '10 plastic from b':6,'10 plastic from f':7,'20 plastic from b':8,'20 plastic from f':9
        ,'5 from b':10,'5 from f':11,'10 from b':12,'10 from f':13,'20 from b':14,'20 from f':15}

def getcode(n) :
    for x , y in code.items() :
        if n == y :
            return x

X_values = []  # Array to save the values of X
plt.figure(figsize=(20, 20))
for i in range(len(X_pred)):
    #plt.subplot(1, len(X_pred), i + 1)
    #plt.imshow(X_pred[i])
    #plt.axis('off')
    X = getcode(np.argmax(y_result[i]))
    #plt.title(X)
    X_values.append(X)  # Append the value of X to the array
#plt.show()  # Display the plot

value_labels = {
    '100 from f': '100 pound',
    '100 from b': '100 pound',
    '200 from b ': '200 pound',
    '200 from f ': '200 pound',
    '50 from b': '50 pound',
    '50 from f': '50 pound',
    '10 plastic from b': '10 plastic pound',
    '10 plastic from f': '10 plastic pound',
    '20 plastic from b': '20 plastic pound',
    '20 plastic from f': '20 plastic pound',
    '5 from b': '5 pound',
    '5 from f': '5 pound',
    '10 from b': '10 pound',
    '10 from f': '10 pound',
    '20 from b': '20 pound',
    '20 from f': '20 pound'
}

counts = Counter(X_values)
most_common_value = counts.most_common(1)[0][0]
count_of_most_common = counts.most_common(1)[0][1]

print("Most repeated value:", most_common_value)
print("Count:", count_of_most_common)

most_common_label = value_labels.get(most_common_value, 'Unknown')
print("Most repeated label:", most_common_label)
AI_speak(most_common_label)

shutil.rmtree( path, ignore_errors=True)  
cv2.destroyAllWindows()
# ==================================================================================
# ==================================================================================
# ==================================================================================



# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
# sns.set(style="whitegrid")
# import os
# import glob as gb
# import cv2
# import tensorflow as tf
# import keras
# import pyttsx3
# import shutil
# import requests


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

# AI_speak("currency recognation has been activated")

# # ======================================================================

# directory =  "predection"  
# parent_dir = (f"C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project")
# #parent_dir = (f"C:\\Users\\user\\Desktop\\predcurrency\\currency_pred")
# path = os.path.join(parent_dir, directory)

# # Check if the directory already exists
# if os.path.exists(path):
#     # If it exists, remove the directory and its contents
#     shutil.rmtree(path)

# os.mkdir(path)
# # ======================================================================

# # عنوان IP لوحدة ESP32-CAM
# # esp32cam_ip = '192.168.100.14/800x800.jpg'
# esp32cam_ip = '192.168.1.104/240x240.jpg'

# # عنوان URL لالتقاط الصورة
# url = f'http://{esp32cam_ip}'

# for i in range(3):  # تكرار العملية مرتين لالتقاط صورتين
#     # إرسال طلب GET لالتقاط الصورة
#     response = requests.get(url)

#     # التحقق من نجاح الطلب
#     if response.status_code == 200:
#         # حفظ الصورة الملتقطة
#         filename = f'C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project\\predection\\mony_{i+1}.jpg'
#         with open(filename, 'wb') as file:
#             file.write(response.content)
#         print(f"picture {i+1} has been successfully")

#         # # عرض الصورة الملتقطة باستخدام OpenCV
#         # image = cv2.imread(filename)
#         # cv2.imshow(f'Captured Image {i+1}', image)
#         # cv2.waitKey(0)
#         # cv2.destroyAllWindows()
#     else:
#         print(f"Failed to take the picture {i+1} ")

# first_image_path = f"C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project\\predection\\mony_1.jpg"
# os.remove(first_image_path)
# print("first picture is delete") 

# # ======================================================================

# # cam = cv2.VideoCapture(0)
# # cv2.waitKey(1000)
# # for i in range(2):
# #        cv2.waitKey(2000)
# #        result, image = cam.read()
# #        cv2.imshow("image", image)
# #        cv2.imwrite(f"%s\image.jpg{i}.jpg"%(path), image)
# #        i =i+1
# #        cv2.destroyWindow("image")


# model = tf.keras.models.load_model("C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project\\model.h5")
# predpath  =(f"C:\\Users\\engmo\\OneDrive\\Documents\\vs code\\project\\")

# files = gb.glob(pathname= str(predpath +'predection/*.jpg'))
# print(f'For Prediction data , found {len(files)}')

# size = []
# files = gb.glob(pathname= str(predpath +'predection/*.jpg'))
# for file in files: 
#     image = plt.imread(file)
#     size.append(image.shape)
# pd.Series(size).value_counts()

# s = 400
# X_pred = []
# files = gb.glob(pathname= str(predpath + 'predection/*.jpg'))
# for file in files: 
#     image = cv2.imread(file)
#     image_array = cv2.resize(image , (s,s))
#     X_pred.append(list(image_array)) 

# print(f'we have {len(X_pred)} items in X_pred')

# plt.figure(figsize=(5,5))
# for n , i in enumerate(list(np.random.randint(0,len(X_pred),2))) : 
#     plt.subplot(2,1,n+1)
#     plt.imshow(X_pred[i])    
#     plt.axis('off')

# X_pred_array = np.array(X_pred)

# y_result = model.predict(X_pred_array)

# print('Prediction Shape is {}'.format(y_result.shape))

# code = {'100 from f':0,'100 from b':1,'200 from b ':2,'200 from f ':3,'50 from b':4,'50 from f':5,
#         '10 plastic from b':6,'10 plastic from f':7,'20 plastic from b':8,'20 plastic from f':9
#         ,'5 from b':10,'5 from f':11,'10 from b':12,'10 from f':13,'20 from b':14,'20 from f':15}

# def getcode(n) :
#     for x , y in code.items() :
#         if n == y :
#             return x
        
# X=getcode(np.argmax(y_result[i])) 
# print(X)
# # def SpeakText(command):
# #     engine = pyttsx3.init()
# #     engine.say(command)
# #     engine.runAndWait()

# AI_speak(X)



# # def SpeakText(command):
# #     engine = pyttsx3.init()
# #     engine.say(command)
# #     engine.runAndWait()


# plt.figure(figsize=(20,20))
# for i in range(len(X_pred)):
#     plt.subplot(1,len(X_pred),i+1)
#     plt.imshow(X_pred[i])    
#     plt.axis('off')
#     X = getcode(np.argmax(y_result[i]))
#     plt.title(X)
 

# shutil.rmtree( path, ignore_errors=True)   
# cv2.destroyAllWindows() 
