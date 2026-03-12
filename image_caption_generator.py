import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2
import tensorflow as tf
from tensorflow.keras.layers import Dense, Flatten, Input, Add, Dropout, LSTM, TimeDistributed, Embedding, RepeatVector, Concatenate
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.sequence import pad_sequences
import os
import glob as gb
import sounddevice as sd
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

AI_speak("Image captioning has been activated")

# ====================================================================== 
# =====================================================================================

url = CAMERA_URL
url = CAMERA_URL
captured_files = []

for i in range(2):  # Try capturing two images
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filename = f'image_caption_{i+1}.jpg'
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
    AI_speak("Error capturing images.")
    exit()

# Delete first picture (buffer clearing)
if os.path.exists(captured_files[0]):
    os.remove(captured_files[0])
    print("First picture deleted.")
                

# ====================================================================== 
       

# Get the image directory path
folder_dir = "images"
images = [image for image in os.listdir(folder_dir)]

# Load captions from file
with open('captions.txt', 'r') as file:
    captions = file.read().split('\n')

# Load pre-trained ResNet50 model
inception_model = ResNet50(include_top=True)
model = Model(inputs=inception_model.input, outputs=inception_model.layers[-2].output)

# Extract features from images
img_features = {}
for img_path in images:
    img = cv2.imread(os.path.join(folder_dir, img_path))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))
    img = img.reshape(1, 224, 224, 3)
    features = model.predict(img).reshape(2048,)
    img_features[img_path] = features

# Preprocess captions
captions = captions[1:]

captions_dict = {}
for cap in captions:
    try:
        img_name, caption = cap.split(',')
        if img_name in img_features:
            if img_name not in captions_dict:
                captions_dict[img_name] = [caption]
            else:
                captions_dict[img_name].append(caption)
    except:
        break

def text_preprocess(text):
    modified_text = text.lower()
    modified_text = 'startofseq ' + modified_text + ' endofseq'
    return modified_text

for key, val in captions_dict.items():
    for item in val:
        captions_dict[key][val.index(item)] = text_preprocess(item)

# Create vocabulary of the entire text corpus
count_words = {}
cnt = 1

for key, val in captions_dict.items():
    for item in val:
        for word in item.split():
            if word not in count_words:
                count_words[word] = cnt
                cnt += 1

# Encode the text
for key, val in captions_dict.items():
    for caption in val:
        encoded = []
        for word in caption.split():
            encoded.append(count_words[word])
        captions_dict[key][val.index(caption)] = encoded

max_len = -1
for key, value in captions_dict.items():
    for caption in value:
        if max_len < len(caption):
            max_len = len(caption)

vocab_size = len(count_words)

def generator(img, caption):
    X = []
    y_input = []
    y_output = []

    for key, val in caption.items():
        for item in val:
            for i in range(1, len(item)):
                X.append(img[key])
                input_seq = [item[:i]]
                output_seq = item[i]
                input_seq = pad_sequences(input_seq, maxlen=max_len, padding='post', truncating='post')[0]
                output_seq = to_categorical([output_seq], num_classes=vocab_size+1)[0]
                y_input.append(input_seq)
                y_output.append(output_seq)

    return X, y_input, y_output

X, y_in, y_out = generator(img_features, captions_dict)
X = np.array(X)
y_in = np.array(y_in, dtype='float64')
y_out = np.array(y_out, dtype='float64')

embedding_len = 128
MAX_LEN = max_len
vocab_size = len(count_words)

# Image feature extraction model
img_model = Sequential()
img_model.add(Dense(embedding_len, input_shape=(2048,), activation='relu'))
img_model.add(RepeatVector(MAX_LEN))

# Caption generation model
captions_model = Sequential()
captions_model.add(Embedding(input_dim=vocab_size+1, output_dim=embedding_len, input_length=MAX_LEN))
captions_model.add(LSTM(256, return_sequences=True))
captions_model.add(TimeDistributed(Dense(embedding_len)))

# Concatenate the outputs of image and caption models
concat_output = Concatenate()([img_model.output, captions_model.output])

# LSTM layers and output layer
output = LSTM(units=128, return_sequences=True)(concat_output)
output = LSTM(units=512, return_sequences=False)(output)
output = Dense(units=vocab_size+1, activation='softmax')(output)

# Final model
final_model = Model(inputs=[img_model.input, captions_model.input], outputs=output)
final_model.compile(loss='categorical_crossentropy', optimizer='RMSprop', metrics='accuracy')

# Load the trained model
final_model.load_weights("image_caption_generator.h5")

# Inverse dictionary for mapping indices back to words
inverse_dict = {val: key for key, val in count_words.items()}

# Generate sample predictions
def get_img(path):
    test_img = cv2.imread(path)
    test_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB)
    test_img = cv2.resize(test_img, (224, 224))
    test_img = np.reshape(test_img, (1, 224, 224, 3))
    return test_img

test_img_path = "image_caption_2.jpg"
test_feature = model.predict(get_img(test_img_path)).reshape(1, 2048)
test_img = cv2.imread(test_img_path)
test_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB)
pred_text = ['startofseq']
count = 0
caption = ''

while count < 25:
    count += 1
    encoded = [count_words[word] for word in pred_text]
    encoded = [encoded]
    encoded = pad_sequences(encoded, maxlen=MAX_LEN, padding='post', truncating='post')
    pred_idx = np.argmax(final_model.predict([test_feature, encoded]))
    sampled_word = inverse_dict[pred_idx]
    if sampled_word == 'endofseq':
        break
    caption = caption + ' ' + sampled_word
    pred_text.append(sampled_word)

AI_speak(caption)

# plt.figure(figsize=(5, 5))
# plt.imshow(test_img)
print(caption)
# plt.xlabel(caption)
# plt.show()
