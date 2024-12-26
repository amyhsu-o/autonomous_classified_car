import cv2 as cv
import numpy as np
from serial import Serial
import os
from time import time
from dotenv import load_dotenv

load_dotenv()

BASE_DISTANCE_INFO = {
    "distance": float(os.getenv("BASE_DISANCE")),
    "radius": float(os.getenv("BASE_RADIUS")),
}
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
        print(f"Send {data} to Arduino")


is_detected = False

cap = cv.VideoCapture(0)

while True:
    frame_time = time()
    ret, frame = cap.read()
    if not ret:
        raise ValueError("Can't receive frame.")

    # frame size
    frame_center_x, frame_center_y = frame.shape[1] // 2, frame.shape[0] // 2
    # print(f"frame center: ({frame_center_x}, {frame_center_y})")

    # turn to hsv
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    # find contours
    edges = cv.Canny(frame, 100, 200)

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
                    distance = (
                        BASE_DISTANCE_INFO["distance"]
                        * radius
                        / BASE_DISTANCE_INFO["radius"]
                    )
                    angle = np.degrees(np.arctan2(x - frame_center_x, distance))
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
