import json
import pathlib
import sys

import cv2
import mediapipe
import numpy as np

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

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            drawing.draw_landmarks(
                image,
                hand_landmarks,
                mediapipe.solutions.hands.HAND_CONNECTIONS,
            )

        bounding_box = [[image.shape[1], image.shape[0]], [0, 0]]
        for world_hand_landmarks in results.multi_hand_landmarks:
            for index, landmark in enumerate(world_hand_landmarks.landmark):
                height, width, _ = image.shape
                cx, cy = int(landmark.x * width), int(landmark.y * height)
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
                if cx < bounding_box[0][0]:
                    bounding_box[0][0] = cx
                if cy < bounding_box[0][1]:
                    bounding_box[0][1] = cy
                if cx > bounding_box[1][0]:
                    bounding_box[1][0] = cx
                if cy > bounding_box[1][1]:
                    bounding_box[1][1] = cy
            cv2.rectangle(
                image,
                (bounding_box[0][0] - 20, bounding_box[0][1] - 20),
                (bounding_box[1][0] + 20, bounding_box[1][1] + 20),
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

            rotated_box_contour = cv2.boxPoints(
                ((cx, cy), (60, 50), angle)
            ).astype(int)
            cv2.drawContours(image, [rotated_box_contour], 0, (255, 0, 0), 2)

            # rotated_box = rotate_rect(
            #     box[0][0], box[0][1], box[1][0], box[1][1], angle,
            # )
            # cv2.rectangle(
            #     image,
            #     (rotated_box[0], rotated_box[1]),
            #     (rotated_box[2], rotated_box[3]),
            #     (255, 0, 0),
            #     2,
            # )

            fingertips_bounding_boxes.append(box)


def rotate_rect(x1, y1, x2, y2, angle):
    """
    Rotates a rectangle defined by (x1, y1, x2, y2) by 'angle' degrees around
    its center.

    Args:
        x1, y1: Coordinates of the top-left corner of the rectangle.
        x2, y2: Coordinates of the bottom-right corner of the rectangle.

        angle: Angle of rotation in degrees.

    Returns:
        Rotated rectangle coordinates (x1_rot, y1_rot, x2_rot, y2_rot).
    """

    # Calculate center of the rectangle
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    # Calculate width and height
    # width = x2 - x1
    # height = y2 - y1

    # Create rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D((center_x, center_y), angle, 1.0)

    # Apply rotation to the corners
    corners = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])

    rotated_corners = (
        np.dot(corners, rotation_matrix[:, :2].T) + rotation_matrix[:, 2]
    )

    # Find new bounding box
    x1_rot, y1_rot = np.min(rotated_corners, axis=0)
    x2_rot, y2_rot = np.max(rotated_corners, axis=0)

    return int(x1_rot), int(y1_rot), int(x2_rot), int(y2_rot)


if "video" in sys.argv:
    cap = cv2.VideoCapture(0)

    while True:
        ret, image = cap.read()
        if not ret:
            continue
        process_image(image)
        cv2.imshow('hand landmarks', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

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
