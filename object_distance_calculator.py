import cv2
import numpy as np
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
    engine.setProperty("rate", 135)
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

AI_speak("Calculating object distance has been activated")

# ======================================================================

url = CAMERA_URL
captured_files = []

for i in range(2):  # Try capturing two images
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filename = f'Calculating_object_distance_{i+1}.jpg'
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
    AI_speak("Error capturing images from camera.")
    exit()

# Delete first picture (buffer clearing)
if os.path.exists(captured_files[0]):
    os.remove(captured_files[0])
    print("First picture deleted.")

# ======================================================================

# Load the YOLOv3 configuration and weights files
model = cv2.dnn.readNet('yolov3.weights', 'yolov3.cfg')

# Get the names of the output layers
layer_names = model.getLayerNames()

# Get the unconnected output layers
unconnected_layers = model.getUnconnectedOutLayers()

# Convert the unconnected layers to a list of tuples
unconnected_layers = [(layer,) for layer in unconnected_layers]

# Get the names of the unconnected output layers
names = [layer_names[i[0] - 1] for i in unconnected_layers]

# Set the real-world width of the object in meters
object_width = 0.2

# Set the focal length of the camera in pixels
focal_length = 615

# Load the list of class names
with open('coco.names.txt', 'r') as f:
    classes = [line.strip() for line in f.readlines()]

# Read the image from a file
image_path = 'Calculating_object_distance_2.jpg'
frame = cv2.imread(image_path)

# Resize the frame to (416, 416)
resized_frame = cv2.resize(frame, (416, 416))

# Create a blob from the frame
blob = cv2.dnn.blobFromImage(resized_frame, 1/255, (416, 416), swapRB=True, crop=False)

# Set the input for the model
model.setInput(blob)

# Forward pass through the model
outputs = model.forward(names)

# Process the outputs
detected_objects = []
for output in outputs:
    # Process detection here
    for detection in output:
        # Get the class ID and confidence score of the current detection
        class_id = np.argmax(detection[5:])
        confidence = detection[5 + class_id]

        if confidence > 0.5:
            # Get the bounding box dimensions
            box = detection[:4] * np.array(
                [resized_frame.shape[1], resized_frame.shape[0], resized_frame.shape[1], resized_frame.shape[0]])
            (center_x, center_y, width, height) = box.astype('int')
            x = int(center_x - (width / 2))
            y = int(center_y - (height / 2))

            # Get the name of the detected object
            class_name = classes[class_id]
            detected_objects.append(class_name)

            # Draw the bounding box and label on the frame
            cv2.rectangle(frame, (x, y), (x + int(width), y + int(height)), (0, 255, 0), 2)
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Estimate the distance of the object from the camera
            distance = (object_width * focal_length) / width
            cv2.putText(frame, f"{distance:.2f} m", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Output the detected objects via voice message
print(f"{class_name} detected at {distance:.2f} meters")
AI_speak(f"{class_name} detected at {distance:.2f} meters")



































# import cv2
# import numpy as np
# import pyttsx3


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

# AI_speak("object detection distance has been activated")

# # ======================================================================
# # Load the YOLOv3 configuration and weights files
# model = cv2.dnn.readNet('yolov3.weights', 'yolov3.cfg')

# # Get the names of the output layers
# layer_names = model.getLayerNames()

# # Get the unconnected output layers
# unconnected_layers = model.getUnconnectedOutLayers()

# # Convert the unconnected layers to a list of tuples
# unconnected_layers = [(layer,) for layer in unconnected_layers]

# # Get the names of the unconnected output layers
# names = [layer_names[i[0] - 1] for i in unconnected_layers]

# # Set the real-world width of the object in meters
# object_width = 0.2

# # Set the focal length of the camera in pixels
# focal_length = 615

# # Load the list of class names
# with open('coco.names.txt', 'r') as f:
#     classes = [line.strip() for line in f.readlines()]

# # Set up the video capture
# cap = cv2.VideoCapture(0)

# # Check if the camera was opened successfully
# if not cap.isOpened():
#     print('Error: Could not open camera')
#     exit()

# # Capture a single frame from the camera
# ret, frame = cap.read()

# # Check if the frame was captured successfully
# if not ret:
#     print('Error: Could not capture frame')
#     exit()

# # Release the video capture
# cap.release()

# # Resize the frame to (416, 416)
# resized_frame = cv2.resize(frame, (416, 416))

# # Create a blob from the frame
# blob = cv2.dnn.blobFromImage(resized_frame, 1/255, (416, 416), swapRB=True, crop=False)

# # Set the input for the model
# model.setInput(blob)

# # Forward pass through the model
# outputs = model.forward(names)

# # Process the outputs
# detected_objects = []
# for output in outputs:
#     # Process detection here
#     for detection in output:
#         # Get the class ID and confidence score of the current detection
#         class_id = np.argmax(detection[5:])
#         confidence = detection[5 + class_id]

#         if confidence > 0.5:
#             # Get the bounding box dimensions
#             box = detection[:4] * np.array(
#                 [resized_frame.shape[1], resized_frame.shape[0], resized_frame.shape[1], resized_frame.shape[0]])
#             (center_x, center_y, width, height) = box.astype('int')
#             x = int(center_x - (width / 2))
#             y = int(center_y - (height / 2))

#             # Get the name of the detected object
#             class_name = classes[class_id]
#             detected_objects.append(class_name)

#             # Draw the bounding box and label on the frame
#             cv2.rectangle(frame, (x, y), (x + int(width), y + int(height)), (0, 255, 0), 2)
#             label = f"{class_name}: {confidence:.2f}"
#             cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#             # Estimate the distance of the object from the camera
#             distance = (object_width * focal_length) / width
#             cv2.putText(frame, f"{distance:.2f} m", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# # Output the detected objects via voice message
# AI_speak(f"{class_name} detected at {distance:.2f} meters")


