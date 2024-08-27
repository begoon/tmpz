import cv2
import numpy as np


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


image = np.zeros((480, 640, 3), np.uint8)

r = [(100, 100), (200, 200)]

cv2.rectangle(image, r[0], r[1], (0, 255, 0), 2)

angle = 0

while True:
    rotated_corners = rotate_rectangle(
        r[0][0], r[0][1], r[1][0], r[1][1], angle
    )
    draw_rectangle_by_corners(image, rotated_corners)
    cv2.imshow("image", image)
    angle += 1

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    draw_rectangle_by_corners(image, rotated_corners, (0, 0, 0))

print("done")
