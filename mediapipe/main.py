import io
import json
import math
import os
import pathlib
import sys

import cv2
import mediapipe
import numpy as np
import requests
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


PALMS_MATCHER_API = os.environ["PALMS_MATCHER_API"]

RED = "\033[31m"
GREEN = "\033[32m"
WHITE = "\033[37m"
YELLOW = "\033[33m"
NC = "\033[0m"

hands = mediapipe.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

drawing = mediapipe.solutions.drawing_utils


def process_image(image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    results = hands.process(image_rgb)

    if not results.multi_hand_landmarks:
        return None, None, None

    bounding_box = [[image.shape[1], image.shape[0]], [0, 0]]

    cropped_image = image.copy()

    for hand_landmarks in results.multi_hand_landmarks:
        drawing.draw_landmarks(
            image,
            hand_landmarks,
            mediapipe.solutions.hands.HAND_CONNECTIONS,
        )

    keypoints = []
    for world_hand_landmarks in results.multi_hand_landmarks[:1]:
        for index, landmark in enumerate(world_hand_landmarks.landmark):
            height, width, _ = image.shape
            cx, cy = int(landmark.x * width), int(landmark.y * height)
            keypoints.append((cx, cy))
            cv2.putText(
                image,
                str(index),
                (cx, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            x_delta = 40
            y_delta = 40
            if cx < bounding_box[0][0]:
                bounding_box[0][0] = max(cx - x_delta, 0)
            if cy < bounding_box[0][1]:
                bounding_box[0][1] = max(cy - y_delta, 0)
            if cx > bounding_box[1][0]:
                bounding_box[1][0] = cx + x_delta
            if cy > bounding_box[1][1]:
                bounding_box[1][1] = cy + y_delta
            height, width, _ = image.shape
            cv2.putText(
                image,
                f"x: {cx}, y: {cy}",
                (0, index * 20 + 20),
                cv2.FONT_HERSHEY_TRIPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.FILLED,
            )
        cv2.rectangle(
            image,
            (bounding_box[0][0], bounding_box[0][1]),
            (bounding_box[1][0], bounding_box[1][1]),
            (0, 255, 0),
            2,
        )

    finger_tips = [4, 8, 12, 16, 20]
    finger_roots = [0, 5, 9, 13, 17]
    fingertips_bounding_boxes = []
    for tip, root in zip(finger_tips, finger_roots):
        angle = cv2.fastAtan2(
            world_hand_landmarks.landmark[root].y
            - world_hand_landmarks.landmark[tip].y,
            world_hand_landmarks.landmark[root].x
            - world_hand_landmarks.landmark[tip].x,
        )
        cx, cy = (
            int(world_hand_landmarks.landmark[tip].x * width),
            int(world_hand_landmarks.landmark[tip].y * height),
        )
        box = [
            [cx - 20, cy - 20],
            [cx + 20, cy + 20],
        ]
        cv2.rectangle(image, box[0], box[1], (0, 0, 255), 2)

        rotated_corners = rotate_rectangle(
            box[0][0]-20, box[0][1], box[1][0]+20, box[1][1], -angle,
        )
        draw_rectangle_by_corners(image, rotated_corners)

        fingertips_bounding_boxes.append(box)

    cropped_image = cropped_image[
        bounding_box[0][1] : bounding_box[1][1],
        bounding_box[0][0] : bounding_box[1][0],
    ]

    x_offset = image.shape[1] - cropped_image.shape[1]
    y_offset = image.shape[0] - cropped_image.shape[0]
    image[y_offset:, x_offset:] = cropped_image

    return image, cropped_image, keypoints


def rotate_rectangle(x1, y1, x2, y2, angle):
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    rotation_matrix = cv2.getRotationMatrix2D((center_x, center_y), angle, 1.0)

    corners = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])

    rotated_corners = (
        np.dot(corners, rotation_matrix[:, :2].T) + rotation_matrix[:, 2]
    ).astype(int)

    return rotated_corners


def draw_rectangle_by_corners(image, corners, color=(0, 255, 0)):
    thickness = 2
    cv2.line(image, corners[0], corners[1], color, thickness)
    cv2.line(image, corners[1], corners[2], color, thickness)
    cv2.line(image, corners[2], corners[3], color, thickness)
    cv2.line(image, corners[3], corners[0], color, thickness)


embeddings = []


class EnrollRequest(BaseModel):
    keypoints: list[tuple[int, int]]


class VerifyRequest(BaseModel):
    keypoints: list[tuple[int, int]]
    embeddings: list[list[float]]


previous_keypoints = []

seconds = 0
last_stable = 0

auto = "auto" in sys.argv

if "video" in sys.argv:
    cap = cv2.VideoCapture(1)

    while True:
        ret, image = cap.read()
        if not ret:
            continue
        preview, cropped_image, keypoints = process_image(image)

        enrolling = False

        if previous_keypoints and keypoints:
            delta = math.sqrt(
                sum(
                    (x1 - x2) ** 2 + (y1 - y2) ** 2
                    for (x1, y1), (x2, y2) in zip(previous_keypoints, keypoints)
                )
            )
            if (delta < 50):
                if seconds - last_stable > 10:
                    print(YELLOW, "STABLE", NC, len(embeddings))
                    last_stable = seconds
                    enrolling = True
            else:
                print(RED, "UNSTABLE", NC)
                last_stable = 0

        previous_keypoints = keypoints

        if preview is not None:
            cv2.imshow('hand landmarks', preview)

        if False and cropped_image is not None:
            cv2.imshow('cropped hand', cropped_image)

        seconds += 1
            
        c = cv2.waitKey(1) & 0xFF
        if c == ord('q'):
            break

        if c == ord('e') or (auto and enrolling):
            print(WHITE, "ENROLL", NC)

            enroll_request = EnrollRequest(keypoints=keypoints)

            image = io.BytesIO(cv2.imencode('.png', cropped_image)[1].tobytes())

            response = requests.post(
                f"{PALMS_MATCHER_API}/enroll",
                data=enroll_request.model_dump(),
                files={
                    'image': image,
                    'request': io.BytesIO(
                        enroll_request.model_dump_json().encode()
                    ),
                },
            )
            response.raise_for_status()
            embedding = response.json()['embedding']

            embeddings.append(embedding)

            print(GREEN, f"{len(embeddings)=}", len(embedding), NC)

        if c == ord('v') or (auto and len(embeddings) >= 10):
            print(WHITE, "VERIFY", NC)

            if len(embeddings) < 1:
                continue

            verify_request = VerifyRequest(
                keypoints=keypoints,
                embeddings=embeddings[-10:],
            )
            print(
                "embeddings",
                YELLOW,
                len(verify_request.embeddings),
                NC,
                "keypoints",
                YELLOW,
                len(verify_request.keypoints),
                NC,
            )

            image = io.BytesIO(cv2.imencode('.png', cropped_image)[1].tobytes())

            files = {
                'image': image,
                'request': io.BytesIO(
                    verify_request.model_dump_json().encode()
                ),
            }

            response = requests.post(
                f"{PALMS_MATCHER_API}/verify",
                data=verify_request.model_dump(),
                files=files,
            )
            response.raise_for_status()
            print("score", GREEN, f"{response.json()["score"]}", NC)

            embeddings = embeddings[:-10]

    cap.release()
    cv2.destroyAllWindows()

if "image" in sys.argv:
    filename = pathlib.Path(sys.argv[2])
    image = cv2.imread(str(filename))
    process_image(image)
    landmarks: list[tuple[int, int]] = json.loads(
        filename.with_suffix('.json').read_text()
    )["keypoints"]
    for index, (x, y) in enumerate(landmarks):
        cv2.circle(image, (x, y), 5, (0, 255, 0), -1)

    cv2.imshow('hand landmarks', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    cv2.imwrite(filename.with_suffix(".output" + filename.suffix), image)
