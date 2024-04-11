# Autonomous-Vehicle-Team-B

Introducing our high-performance autonomous RC car, masterfully piloted by the iconic Dominic Toretto. Engineered for versatility, it thrives on diverse terrains with advanced obstacle avoidance, sign detection, and lane keeping. At its core, powerful motors and a sophisticated turning mechanism ensure dynamic mobility, while a 12V battery and Raspberry Pi brain equip it with formidable power and intelligence. This vehicle isn't just about getting from A to B; it's about the journey in between, redefining what it means to drive autonomously.

## Prerequisites

Before you can run this project, you'll need the following installed:

- Python 3.6 or higher
- OpenCV-Python
- picamera2 (specific to Raspberry Pi OS)
- RPi.GPIO (specific to Raspberry Pi)
- asyncio library (should be included with Python 3.6+)

You can install Python from [the official website](https://www.python.org/downloads/).

## Installation

1. **OpenCV-Python**: Install OpenCV for Python by running:

   ```
   pip install opencv-python
   ```

2. **picamera2**: For Raspberry Pi, install the picamera2 library using:

   ```
   sudo apt-get update
   sudo apt-get install python3-picamera2
   ```

3. **RPi.GPIO**: This should come pre-installed with Raspberry Pi OS. If you need to install it, use:

   ```
   sudo apt-get install python3-rpi.gpio
   ```

## Training Cascade Classifiers

Training your own cascade classifiers with OpenCV involves several steps. You will need a set of positive images (images of your object) and negative images (images without your object). Follow these steps:

1. **Collect Images**: Gather a dataset of positive and negative images. Positive images should contain the object you want to detect, and negative images should not.

2. **Annotation**: Use an annotation tool to mark the object in each positive image. One such tool is `labelImg`.

   - Installation: `pip install labelImg`
   - Usage: Run `labelImg`, open your dataset, and start annotating.

3. **Create Samples**: Use OpenCV's `opencv_createsamples` utility to create a vector file from your annotated positive images.

   ```
   opencv_createsamples -info annotations.txt -num 1000 -w 20 -h 20 -vec positives.vec
   ```

4. **Train Cascade**: With the positive vector file and the collection of negative images, you can train the cascade classifier.

   ```
   opencv_traincascade -data cascade_directory -vec positives.vec -bg negatives.txt -numPos 800 -numNeg 400 -numStages 10 -w 20 -h 20
   ```

   Adjust the `numPos`, `numNeg`, and `numStages` parameters based on your dataset.

## Wiring Instructions

The code provided controls a Raspberry Pi-based robot with obstacle detection, line tracking, and basic navigation features. Here's a summary of the wiring based on the GPIO pins defined in your code:

- **Motors**:
  - `motorIn1`, `motorIn2`: Connect to the left motor.
  - `motorIn3`, `motorIn4`: Connect to the right motor.
  - `enL`, `enR`: Connect to the enable pins on your motor driver to control speed.

- **LEDs**:
  - `LEFT`, `RIGHT`: Connect to LEDs that indicate turning direction.

- **Ultrasonic Sensor**:
  - `TRIG`: Connect to the trigger pin.
  - `ECHO`: Connect to the echo pin.

## Project Files Overview

- **`Camera_Drive_Merge.py`**: This is the final competition code and the main file to run everything. It integrates camera-based signal detection with driving functions.
- **`async.py`**: Contains the driving function for the first competition, which is focused on basic driving without camera integration.
- **`signal_detection2.py`**: Used for testing multiple cascades for image detection. It allows you to test the performance of different cascades in recognizing various signals.
- **`signal_detection1.py`**: Designed for testing a single cascade. This script is useful for focused testing on one particular type of signal.
- **XML Files**: These are the cascade files used for image detection. They should be trained as described in the "Training Cascade Classifiers" section and placed in the same directory as your Python scripts for the project.

Please make sure to place all your scripts and XML files in the same directory and run `Camera_Drive_Merge.py` as the main script to start the project.
