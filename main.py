import cv2 as cv
import numpy as np
from serial import Serial
import os
from time import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WINDOW_NAME = "frame"

if os.getenv("ARDUINO_CONNECTED") == "True":
    arduino = Serial(os.getenv("SERIAL_PORT"), baudrate=9600, timeout=1)

last_send_frame_time = time()


def send_message_to_arduino(data):
    if os.getenv("ARDUINO_CONNECTED") == "True":
        if arduino.isOpen():
            arduino.write(str(data).encode())
            print(f"Sent to Arduino: {data}")
            arduino.flush()
        else:
            print("Serial port is not open.")
    else:
        print(f"{datetime.now()}\nSend {data} to Arduino")


def get_distance(frame_width, radius):
    # distance = -\frac{w_{real} * W_{frame}}{2 * w_{pixels} * tan(HFOV / 2)}
    w_real = float(os.getenv("BALL_DIAMETER"))
    HFOV = float(os.getenv("HFOV"))
    distance = -(w_real * frame_width) / (2 * radius * np.tan(HFOV / 2))
    return float(distance)


def get_angle(frame_width, x):
    # angle = \frac{\delta x}{W_{frame} * HFOV
    HFOV = float(os.getenv("HFOV"))
    angle = (x - frame_width / 2) / frame_width * HFOV
    return float(angle)


is_detected = False

cap = cv.VideoCapture(0)

while True:
    frame_time = time()
    ret, frame = cap.read()
    if not ret:
        raise ValueError("Can't receive frame.")

    # turn to hsv
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    # color info
    red_lower = np.array([0, 120, 70])
    red_upper = np.array([10, 255, 255])
    yellow_lower = np.array([20, 100, 100])
    yellow_upper = np.array([30, 255, 255])
    blue_lower = np.array([100, 150, 0])
    blue_upper = np.array([140, 255, 255])

    red_mask = cv.inRange(hsv, red_lower, red_upper)
    yellow_mask = cv.inRange(hsv, yellow_lower, yellow_upper)
    blue_mask = cv.inRange(hsv, blue_lower, blue_upper)

    color_info = {
        "red": {
            "lower": red_lower,
            "upper": red_upper,
            "border_color": (26, 26, 154),
            "mask": red_mask,
        },
        "yellow": {
            "lower": yellow_lower,
            "upper": yellow_upper,
            "border_color": (51, 153, 255),
            "mask": yellow_mask,
        },
        "blue": {
            "lower": blue_lower,
            "upper": blue_upper,
            "border_color": (161, 28, 28),
            "mask": blue_mask,
        },
    }

    # find color in contours
    detected_balls = []
    for color, info in color_info.items():
        contours, _ = cv.findContours(
            info["mask"], cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE
        )
        for contour in contours:
            if cv.contourArea(contour) > 500:
                ((x, y), radius) = cv.minEnclosingCircle(contour)
                if radius > 5:
                    cv.circle(
                        frame, (int(x), int(y)), int(radius), info["border_color"], 2
                    )
                    distance = get_distance(frame.shape[1], radius)
                    angle = get_angle(frame.shape[1], x)

                    # print(f"\n===== {color} =====")
                    # print(f"coord: ({x}, {y})")
                    # print(f"radius: {radius}")
                    # print(f"distance: {distance}")
                    # print(f"angle: {angle}°")
                    # print("-" * 20)

                    detected_balls.append(
                        {
                            "color": ["red", "yellow", "blue"].index(color),
                            "radius": radius,
                            "dist": distance,
                            "angle": float(angle),
                        }
                    )

    # return the nearest ball
    detected_balls = sorted(detected_balls, key=lambda x: x["radius"], reverse=True)
    if len(detected_balls) > 0 and (
        not is_detected or (frame_time - last_send_frame_time) >= 5
    ):
        is_detected = True
        last_send_frame_time = frame_time

        nearest_ball = detected_balls[0]
        del nearest_ball["radius"]
        send_message_to_arduino(nearest_ball)
    elif len(detected_balls) == 0:
        is_detected = False

    # check exit
    cv.imshow(WINDOW_NAME, frame)

    if cv.waitKey(1) == 27:
        print("Press esc to exit")
        break

    if cv.getWindowProperty(WINDOW_NAME, cv.WND_PROP_VISIBLE) < 1:
        print("Click 'x' to exit")
        break

cap.release()
cv.destroyAllWindows()
