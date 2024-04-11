import asyncio
import cv2
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
SERVO = 11  # Servo pin

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

# Global variable for detected sign and a lock for thread-safe access
detected_sign = None
lock = asyncio.Lock()

# Asynchronous function for ultrasonic sensor checking
async def ULT_CHECK():
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

# Asynchronous function for line tracking
async def LINETRACK():
    left_sensor_active = GPIO.input(leftTrack) == 0  # is black
    right_sensor_active = GPIO.input(rightTrack) == 0  #0 is black

    if left_sensor_active and not right_sensor_active:
        print("Adjusting Right")
        GPIO.output(RIGHT, 1) 
        servo.ChangeDutyCycle(8.5)
        await asyncio.sleep(0.5)
        GPIO.output(RIGHT, 0)  

    elif not left_sensor_active and right_sensor_active:
        print("Adjusting Left")
        GPIO.output(LEFT, 1) 
        servo.ChangeDutyCycle(6.5)
        await asyncio.sleep(0.5)
        GPIO.output(LEFT, 0)

    else:
        pL.ChangeDutyCycle(5)
        pR.ChangeDutyCycle(5)

    await asyncio.sleep(0.1)

# Asynchronous function for stopping and waiting when a stop sign is detected
async def STOP_AND_WAIT():
    print("Stop sign detected, stopping")
    while dist <= 5:
        GPIO.output(LEFT, 1)
        GPIO.output(RIGHT, 1)
        await asyncio.sleep(0.5)
        GPIO.output(LEFT, 0)
        GPIO.output(RIGHT, 0)
        await asyncio.sleep(0.5)

# Asynchronous function for object detection
async def detect_objects():
    global detected_sign
    try:
        while True:
            im = picam2.capture_array()
            grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            new_sign = None

            for direction, cascade in face_cascades.items():
                detections = cascade.detectMultiScale(grey, 1.1, 5)
                if len(detections) > 0:
                    new_sign = direction
                    break  # Consider the first detected sign

            async with lock:
                if new_sign != detected_sign:
                    detected_sign = new_sign  # Update the global detected_sign variable
            
            await asyncio.sleep(0)  # Yield control to allow other tasks to run
    finally:
        picam2.stop()
        cv2.destroyAllWindows()

# Asynchronous function for driving the vehicle
async def DRIVE():
    global detected_sign
    while True:
        await ULT_CHECK()  # Continuously check for obstacles
        await LINETRACK()  # Stay within the lane

        async with lock:  # Access the detected_sign in a thread-safe manner
            current_sign = detected_sign

        if current_sign == "stopsign":
            print("Stop sign detected, stopping the car")
            # Stop the car by setting motor speeds to 0
            pL.ChangeDutyCycle(0)
            pR.ChangeDutyCycle(0)
            await STOP_AND_WAIT()  # You might want to wait for a bit after stopping

        elif current_sign == "left":
            print("Left sign detected, turning left")
            # Adjust the servo for a left turn
            servo.ChangeDutyCycle(6.5)  # Adjust this value based on your servo setup
            await asyncio.sleep(1)  # Adjust this sleep time based on how sharp you want the turn to be

        elif current_sign == "right":
            print("Right sign detected, turning right")
            # Adjust the servo for a right turn
            servo.ChangeDutyCycle(8.5)  # Adjust this value based on your servo setup
            await asyncio.sleep(1)  # Adjust this sleep time based on how sharp you want the turn to be

        # Reset the detected_sign to None after handling
        async with lock:
            detected_sign = None

        # Add logic to continue driving forward or any other default behavior
        # For example, setting motors to drive straight ahead at a standard speed
        pL.ChangeDutyCycle(25)  # Adjust these values based on your setup and desired speed
        pR.ChangeDutyCycle(25)
        servo.ChangeDutyCycle(7.5)  # Adjust to set servo back to straight-ahead position

        await asyncio.sleep(0.1)  # Small delay to allow other tasks to run

# Main function to execute the driving logic and object detection concurrently
async def main():
    detect_task = asyncio.create_task(detect_objects())
    drive_task = asyncio.create_task(DRIVE())
    await asyncio.gather(detect_task, drive_task)

# Execute the main function
if __name__ == "__main__":
    asyncio.run(main())
