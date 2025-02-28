import sys
from pathlib import Path

import cv2
import mediapipe


def landmarks(input_file: str) -> None:
    output_path = Path(input_file).stem + "_output" + Path(input_file).suffix
    mediapipe_hands = mediapipe.solutions.hands
    hands = mediapipe_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.1,
    )

    image = cv2.imread(input_file)
    assert image is not None, f"error reading image {input_file=}"

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    results = hands.process(image_rgb)

    assert results.multi_hand_landmarks, "no hands detected in the image"

    for landmarks in results.multi_hand_landmarks:
        for i, landmark in enumerate(landmarks.landmark):
            h, w, _ = image.shape
            cx, cy = int(landmark.x * w), int(landmark.y * h)

            cv2.circle(
                image,
                (cx, cy),
                radius=5,
                color=(0, 255, 0),
                thickness=-1,
            )

            print(
                f"landmark {i}: "
                f"(x={landmark.x:.4f}, y={landmark.y:.4f}, z={landmark.z:.4f})"
            )

    cv2.imwrite(output_path, image)
    print(f"annotated image saved {output_path=}")


def main():
    print(sys.argv)
    input_image = sys.argv[1] if len(sys.argv) > 1 else "image.png"
    landmarks(input_image)


if __name__ == "__main__":
    main()
