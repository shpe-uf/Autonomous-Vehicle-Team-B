#!/usr/bin/python3

import cv2
from picamera2 import Picamera2

# Initialize face cascade classifiers
face_cascades = {
    "right": cv2.CascadeClassifier("cascade_right.xml"),
    "left": cv2.CascadeClassifier("newLeft.xml"),
    "stopsign": cv2.CascadeClassifier("stop_OG.xml")
}

# Start window thread
cv2.startWindowThread()

# Initialize PiCamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# Decrease the frame rate to 4fps
Picamera2.framerate=4


while True:
    # Capture image
    im = picam2.capture_array()
    
    # Convert image to grayscale
    grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    detections = {"right": [], "left": [], "stopsign": []}
    for direction, cascade in face_cascades.items():
        detections[direction] = cascade.detectMultiScale(grey, 1.1, 5)
        # Draw rectangles around detected faces
    for direction, faces in detections.items():
        for (x, y, w, h) in faces:
            cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(im, direction, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            if direction == "right":
                print("right turn")
            elif direction == "stopsign":
                print("stop sign")
            elif direction == "left":
                print("left") 
            

    # Display the image
    cv2.imshow("Camera", im)
    
    # Wait for 1ms and check for the 'q' key to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
picam2.stop()
cv2.destroyAllWindows()
