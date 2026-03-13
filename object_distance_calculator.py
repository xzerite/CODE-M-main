import cv2
import numpy as np
import requests
import os
from config import CAMERA_URL, USE_DEVICE_CAMERA, capture_from_device
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

captured_files = []
if USE_DEVICE_CAMERA:
    captured_files = capture_from_device(2, 0.4)
    for i in range(len(captured_files)):
        print(f"Picture {i+1} has been successfully captured (device camera).")
else:
    url = CAMERA_URL
    for i in range(2):
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
            print(f"Error connecting to camera for picture {i+1}: {e}")

if not captured_files:
    print("Error: Could not capture any images from camera.")
    AI_speak("Error capturing images from camera.")
    exit()

# Use the last captured image for processing
img_to_use = captured_files[-1]
print(f"Using {img_to_use} for processing.")

# Cleanup other captured files if any
for f in captured_files:
    if f != img_to_use and os.path.exists(f):
        os.remove(f)
        print(f"Cleaned up temporary file: {f}")

# ======================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))
yolov3_weights = os.path.join(script_dir, 'yolov3.weights')
yolov3_cfg = os.path.join(script_dir, 'yolov3.cfg')
coco_names = os.path.join(script_dir, 'coco.names.txt')
if not os.path.isfile(coco_names):
    coco_names = os.path.join(script_dir, 'coco.names')

if not os.path.isfile(yolov3_weights) or not os.path.isfile(yolov3_cfg):
    print("Error: YOLOv3 files missing. Put yolov3.weights and yolov3.cfg in the project folder.")
    AI_speak("Object distance model files are missing. Add yolov3 weights and config.")
    exit()
if not os.path.isfile(coco_names):
    print("Error: coco.names or coco.names.txt not found in project folder.")
    AI_speak("Class names file is missing.")
    exit()

# Load the YOLOv3 configuration and weights files
model = cv2.dnn.readNet(yolov3_weights, yolov3_cfg)

# Get the names of the output layers
layer_names = model.getLayerNames()
unconnected_layers = model.getUnconnectedOutLayers()
unconnected_layers = [(layer,) for layer in unconnected_layers]
names = [layer_names[i[0] - 1] for i in unconnected_layers]

# Set the real-world width of the object in meters
object_width = 0.2
# Set the focal length of the camera in pixels
focal_length = 615

# Load the list of class names
with open(coco_names, 'r') as f:
    classes = [line.strip() for line in f.readlines()]

# Read the image from a file
image_path = img_to_use
frame = cv2.imread(image_path)
if frame is None:
    print(f"Error: Could not read image from {image_path}")
    AI_speak("Could not load the captured image.")
    exit()

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


