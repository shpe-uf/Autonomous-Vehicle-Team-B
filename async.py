#pasted
import RPi.GPIO as GPIO
import time
import asyncio
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
angle = 2  # This variable is unused in your original code
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

pL.start(100)
pR.start(100)
servo.start(0)  # Initialize servo to 0 degrees

async def ULT_CHECK():
    global dist
    #Check how far ultrasonic sensor is from object
    print("Measuring")
    GPIO.output(TRIG, 1)
    await asyncio.sleep(0.000001)
    GPIO.output(TRIG, 0)
    
    while GPIO.input(ECHO) == 0:
        pass
    start = time.time()
    
    while GPIO.input(ECHO) == 1:
        pass
    stop = time.time()
    dist = int((stop - start) * 17000)
    
    #print(f"start: {start} and stop: {stop}")
    #print(f"distance: {dist}")

async def LINETRACK():
	left_sensor_active = GPIO.input(leftTrack) == 0  # Assuming 0 is black
	right_sensor_active = GPIO.input(rightTrack) == 0  # Assuming 0 is black

	if left_sensor_active and not right_sensor_active:
		# Left sensor on black, right sensor not on black - turn right, speed up left motor, slow down right motor
		print("Adjusting Right")
		GPIO.output(RIGHT, 1)  # Turn RIGHT LED on
		await asyncio.sleep(0.5)

		servo.ChangeDutyCycle(8.5)
		    
		await asyncio.sleep(0.5)
		GPIO.output(RIGHT, 0)  # Turn RIGHT LED off
		await asyncio.sleep(0.5)

	elif not left_sensor_active and right_sensor_active:
		# Right sensor on black, left sensor not on black - turn left, speed up right motor, slow down left motor
		print("Adjusting Left")
		GPIO.output(LEFT, 1)  # Turn LEFT LED on
		# Speed up right motor
		await asyncio.sleep(0.5)

		servo.ChangeDutyCycle(6.5)

		await asyncio.sleep(0.5)
		GPIO.output(LEFT, 0)  # Turn LEFT LED off
		await asyncio.sleep(0.5)

	else:
		# Both sensors not on black - continue moving forward
		pL.ChangeDutyCycle(25)
		pR.ChangeDutyCycle(25)
		GPIO.output(LEFT, 0)  # Ensure LEFT LED is off
		GPIO.output(RIGHT, 0)  # Ensure RIGHT LED is off
		servo.ChangeDutyCycle(7.5)


	await asyncio.sleep(0.1)





async def STOP_AND_WAIT():
    print("STOP")
    # LED stop signal, flashing while stopped
    while dist <= 5:
        await ULT_CHECK()  # Continuously check distance
        GPIO.output(LEFT, 1)
        GPIO.output(RIGHT, 1)
        await asyncio.sleep(0.5)  # Adjust flash speed as necessary
        GPIO.output(LEFT, 0)
        GPIO.output(RIGHT, 0)
        await asyncio.sleep(0.5)  # Adjust flash speed as necessary

async def DRIVE():
    # Start driving the motor

    GPIO.output(motorIn1, GPIO.HIGH)
    GPIO.output(motorIn2, GPIO.LOW)
    GPIO.output(motorIn3, GPIO.HIGH)
    GPIO.output(motorIn4, GPIO.LOW)

    while True:
        await ULT_CHECK()  # Check distance using the ultrasonic sensor
        await LINETRACK()  # Check line tracking sensors and adjust LED

        if dist >= 5:
            # If object is more than 5 units away, keep driving forward
            print('Driving')
            pL.ChangeDutyCycle(50)
            pR.ChangeDutyCycle(50)
            GPIO.output(motorIn1, GPIO.HIGH)
            GPIO.output(motorIn2, GPIO.LOW)
            GPIO.output(motorIn3, GPIO.HIGH)
            GPIO.output(motorIn4, GPIO.LOW)
        else:
            # If object is closer than 5 units, stop
            GPIO.output(motorIn1, GPIO.LOW)
            GPIO.output(motorIn2, GPIO.LOW)
            GPIO.output(motorIn3, GPIO.LOW)
            GPIO.output(motorIn4, GPIO.LOW)
            await STOP_AND_WAIT()
	    



async def main():
    # Main function to execute the driving logic
    await DRIVE()

# Execute the main function
if __name__ == "__main__":
    print('start')
    
    print('running')
    pL.start(100)
    pR.start(100)
   
    asyncio.run(main())
