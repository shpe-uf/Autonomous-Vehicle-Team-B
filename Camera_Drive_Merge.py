import cv2
import asyncio
import time
from picamera2 import Picamera2
import RPi.GPIO as GPIO

# Set GPIO mode to BOARD
GPIO.setmode(GPIO.BOARD)

# Pin Definitions
LEFT = 3  # Left indicator LED
RIGHT = 5  # Right indicator LED
TRIG = 8  # Ultrasonic sensor trigger pin
ECHO = 7  # Ultrasonic sensor echo pin
motorIn1 = 37  # Left motor input 1
motorIn2 = 40  # Left motor input 2
enL = 33  # Left motor enable pin
motorIn3 = 35  # Right motor input 1
motorIn4 = 36  # Right motor input 2
enR = 38  # Right motor enable pin
SERVO = 32  # Servo motor control pin

# Initialize GPIO pins
GPIO.setup([motorIn1, motorIn2, motorIn3, motorIn4, enL, enR, LEFT, RIGHT, TRIG, SERVO], GPIO.OUT)
GPIO.setup([ECHO], GPIO.IN)

# Set initial state of pins
GPIO.output([motorIn1, motorIn2, motorIn3, motorIn4, LEFT, RIGHT, TRIG], GPIO.LOW)

# Setup PWM for motors and servo
pL = GPIO.PWM(enL, 1000)  # Left motor PWM
pR = GPIO.PWM(enR, 1000)  # Right motor PWM
servo = GPIO.PWM(SERVO, 50)  # Servo PWM (50Hz for servo control)

# Start PWM with initial duty cycle
pL.start(25)
pR.start(25)
servo.start(0)  # Initialize servo position

# Initialize camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# Load cascade classifiers for sign detection
face_cascades = {
    "right": cv2.CascadeClassifier("cascade_right.xml"),
    "left": cv2.CascadeClassifier("leftOld.xml"),
    "stopsign": cv2.CascadeClassifier("stop_OG.xml")
}

# Detect objects asynchronously
async def detect_objects():
    global detected_sign  # Track detected signs globally
    servo.ChangeDutyCycle(7.5)  # Center servo initially

    detection_counter = 0  # Counter for consecutive detections
    no_sign_counter = 0  # Counter for non-detections
    DEBOUNCE_THRESHOLD = 7  # Required consecutive detections to act

    try:
        while True:
            image = picam2.capture_array()  # Capture image from camera
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert to grayscale for detection

            # Initialize detection dict
            detections = {"right": [], "left": [], "stopsign": []}
            sign_detected = False

            # Loop through each cascade to detect signs
            for direction, cascade in face_cascades.items():
                detections[direction] = cascade.detectMultiScale(gray_image, 1.1, 5)
                if detections[direction]:
                    detected_sign = direction
                    sign_detected = True

                    # Perform actions based on detected sign and debounce count
                    if detected_sign == "stopsign" and detection_counter >= DEBOUNCE_THRESHOLD:
                        await STOP()  # Stop if stop sign detected after sufficient debouncing
                        detection_counter = 0  # Reset counter after action

                    elif detected_sign == "left" and detection_counter >= DEBOUNCE_THRESHOLD:
                        # Turn left if left sign detected after sufficient debouncing
                        GPIO.output(LEFT, GPIO.HIGH)
                        servo.ChangeDutyCycle(6.5)  # Adjust servo for left turn
                        await asyncio.sleep(0.5)  # Wait for turn to complete
                        GPIO.output(LEFT, GPIO.LOW)
                        
                    elif detected_sign == "right" and detection_counter >= DEBOUNCE_THRESHOLD:
                        # Turn right if right sign detected after sufficient debouncing
                        GPIO.output(RIGHT, GPIO.HIGH)
                        servo.ChangeDutyCycle(8.5)  # Adjust servo for right turn
                        await asyncio.sleep(0.5)  # Wait for turn to complete
                        GPIO.output(RIGHT, GPIO.LOW)

            # Update counters based on detection
            detection_counter = detection_counter + 1 if sign_detected else 0
            no_sign_counter = no_sign_counter + 1 if not sign_detected else 0

            # Default forward motion if no sign detected for a while
            if no_sign_counter >= DEBOUNCE_THRESHOLD:
                await FORWARD()
                no_sign_counter = 0

            # Distance measurement logic
            global dist
            # Trigger ultrasonic sensor
            GPIO.output(TRIG, True)
            await asyncio.sleep(0.000001)
            GPIO.output(TRIG, False)

            # Measure echo time
            while GPIO.input(ECHO) == 0: pass
            start_time = time.time()
            while GPIO.input(ECHO) == 1: pass
            stop_time = time.time()

            # Calculate distance
            dist = (stop_time - start_time) * 17000

            # Stop if an obstacle is too close
            if dist <= 10:
                await STOP()
                
            # Highlight detected signs in the output video
            for direction, faces in detections.items():
                for (x, y, w, h) in faces:
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(image, direction, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Show the processed video output
            cv2.imshow("Camera", image)

            # Break the loop with 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Clean up
        picam2.stop()
        cv2.destroyAllWindows()

# Function to move the car forward
async def FORWARD():
    # Activate motors for forward motion
    GPIO.output(motorIn1, GPIO.HIGH)
    GPIO.output(motorIn2, GPIO.LOW)
    GPIO.output(motorIn3, GPIO.HIGH)
    GPIO.output(motorIn4, GPIO.LOW)
    pL.ChangeDutyCycle(25)  # Set speed
    pR.ChangeDutyCycle(25)
    
# Function to stop the car
async def STOP():
    # Deactivate all motors
    GPIO.output([motorIn1, motorIn2, motorIn3, motorIn4], GPIO.LOW)
    # Briefly flash LEDs to indicate stopping
    GPIO.output([LEFT, RIGHT], GPIO.HIGH)
    await asyncio.sleep(0.5)
    GPIO.output([LEFT, RIGHT], GPIO.LOW)
    await asyncio.sleep(0.5)
    
# Main function combining driving logic and object detection
async def main():
    await detect_objects()

# Execute main function
if __name__ == "__main__":
    asyncio.run(main())
