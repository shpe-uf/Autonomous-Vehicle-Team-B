import cv2
import asyncio
import time
from picamera2 import Picamera2
import RPi.GPIO as GPIO

# Setup GPIO mode
GPIO.setmode(GPIO.BOARD)

# Define GPIO pins
LEFT = 3  # Left LED
RIGHT = 5  # Right LED
TRIG = 8
ECHO = 7
motorIn1 = 37  # Left motor
motorIn2 = 40  # Left motor
enL = 33
motorIn3 = 35  # Right motor
motorIn4 = 36  # Right motor
enR = 38
turn_time_delay = 0.3
dist = 0
leftTrack = 10
rightTrack = 12
SERVO = 32  # Servo pin
global detected_sign


# Setup GPIO pins
GPIO.setup([motorIn1, motorIn2, motorIn3, motorIn4, enL, enR, LEFT, RIGHT, TRIG, SERVO], GPIO.OUT)
GPIO.setup([ECHO, leftTrack, rightTrack], GPIO.IN)

# Initialize pins to low
GPIO.output([motorIn1, motorIn2, motorIn3, motorIn4, LEFT, RIGHT, TRIG], GPIO.LOW)

# Setup PWM
pL = GPIO.PWM(enL, 1000)
pR = GPIO.PWM(enR, 1000)
servo = GPIO.PWM(SERVO, 50)  # 50Hz for servo

pL.start(25)
pR.start(25)
servo.start(0)  # Initialize servo to 0 degrees

# Initialize PiCamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()


# Initialize face cascade classifiers
face_cascades = {
    "right": cv2.CascadeClassifier("cascade_right.xml"),
    "left": cv2.CascadeClassifier("leftOld.xml"),
    "stopsign": cv2.CascadeClassifier("stop_OG.xml")
}



# Asynchronous function for object detection
async def detect_objects():
    global detected_sign  # Use global variable to track detected signs
    servo.ChangeDutyCycle(7.5)  # Center the servo
    detection_counter = 0  # Counter to keep track of continuous detections
    no_sign_counter = 0  # Counter to keep track of continuous non-detections
    DEBOUNCE_THRESHOLD = 7 # Number of continuous detections needed before acting

    try:
        while True:
            im = picam2.capture_array()  # Capture image from PiCamera
            grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
            detections = {"right": [], "left": [], "stopsign": []}
            sign_detected = False

            # Detect signs using cascades
            for direction, cascade in face_cascades.items():
                detections[direction] = cascade.detectMultiScale(grey, 1.1, 5)
                if len(detections[direction]) > 0:
                    detected_sign = direction
                    sign_detected = True
                    if detected_sign == "stopsign" and detection_counter >= DEBOUNCE_THRESHOLD:
                        await STOP()
                        detection_counter = 0  # Reset the counter after taking action
                        sign_detected = False
                        
                    elif detected_sign == "left" and detection_counter >= DEBOUNCE_THRESHOLD:
                        print("Adjusting Left")
                        GPIO.output(LEFT, GPIO.HIGH)
                        servo.ChangeDutyCycle(6.5)  # Turn left
                        await asyncio.sleep(0.5)
                        GPIO.output(LEFT, GPIO.LOW)
                        
                    elif detected_sign == "right" and detection_counter >= DEBOUNCE_THRESHOLD:
                        print("Adjusting Right")
                        GPIO.output(RIGHT, GPIO.HIGH)
                        servo.ChangeDutyCycle(8.5)  # Turn right
                        await asyncio.sleep(0.5)
                        GPIO.output(RIGHT, GPIO.LOW)
                        
            # Increment or reset detection counter based on whether a sign was detected
            if sign_detected:
                detection_counter += 1
                no_sign_counter = 0  # Reset no-sign counter when a sign is detected
            
            else:
                detection_counter = 0  # Reset detection counter when no sign is detected
                no_sign_counter += 1

            # Line sensor logic integrated with object detection
            left_sensor_active = GPIO.input(leftTrack) == 0  # Left sensor reads black
            right_sensor_active = GPIO.input(rightTrack) == 0  # Right sensor reads black

            if left_sensor_active and not right_sensor_active and not sign_detected:
                print("Adjusting Right")
                GPIO.output(RIGHT, GPIO.HIGH)
                servo.ChangeDutyCycle(8.5)  # Turn right
                await asyncio.sleep(0.5)
                GPIO.output(RIGHT, GPIO.LOW)

            elif not left_sensor_active and right_sensor_active and not sign_detected:
                print("Adjusting Left")
                GPIO.output(LEFT, GPIO.HIGH)
                servo.ChangeDutyCycle(6.5)  # Turn left
                await asyncio.sleep(0.5)
                GPIO.output(LEFT, GPIO.LOW)
            elif not sign_detected:
                servo.ChangeDutyCycle(7.5)
                
            # Drive forward if no sign is detected
            if no_sign_counter >= DEBOUNCE_THRESHOLD:
                await FORWARD()
                no_sign_counter = 0

            global dist
            print("Measuring distance")
            GPIO.output(TRIG, 1)
            await asyncio.sleep(0.000001)
            GPIO.output(TRIG, 0)

            while GPIO.input(ECHO) == 0:
                pass
            start = time.time()

            while GPIO.input(ECHO) == 1:
                pass
            stop = time.time()
            dist = (stop - start) * 17000
            print(dist)
            
            if dist <= 10:
                await STOP()
                
            # Display detected objects with rectangles
            for direction, faces in detections.items():
                for (x, y, w, h) in faces:
                    cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(im, direction, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            cv2.imshow("Camera", im)

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Exit loop if 'q' is pressed
                break

    finally:
        picam2.stop()
        cv2.destroyAllWindows()


async def FORWARD():
    print("Driving")
    GPIO.output(motorIn1, GPIO.HIGH)
    GPIO.output(motorIn2, GPIO.LOW)
    GPIO.output(motorIn3, GPIO.HIGH)
    GPIO.output(motorIn4, GPIO.LOW)
    pL.ChangeDutyCycle(25)
    pR.ChangeDutyCycle(25)
    
    
async def STOP():
    print("Inside Stop and Wait (waiting...)")
    GPIO.output(motorIn1, GPIO.LOW)
    GPIO.output(motorIn2, GPIO.LOW)
    GPIO.output(motorIn3, GPIO.LOW)
    GPIO.output(motorIn4, GPIO.LOW)
    GPIO.output(LEFT, 1)
    GPIO.output(RIGHT, 1)
    await asyncio.sleep(0.5)
    GPIO.output(LEFT, 0)
    GPIO.output(RIGHT, 0)
    await asyncio.sleep(0.5)
    
# Main function to execute the driving logic and object detection concurrently
async def main():
# = asyncio.create_task(detect_objects())
#ask2 = asyncio.create_task(DRIVE())
#wait asyncio.gather(task1, task2)
    await detect_objects()
# Execute the main function
if __name__ == "__main__":

    asyncio.run(main())
