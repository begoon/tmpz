import cv2

img = cv2.imread("birds.jpeg")
print(img.shape)
h, w, c = img.shape
print(f'h: {h}, w: {w}, c: {c}')

cv2.rectangle(img, (0, 0), (img.shape[1], img.shape[0]), (0, 255, 0), 10)
text_height = 100
scale = cv2.getFontScaleFromHeight(
    cv2.FONT_HERSHEY_SIMPLEX,
    text_height,
    thickness=2,
)
text_size, baseline = cv2.getTextSize(
    "Birds".upper(),
    cv2.FONT_HERSHEY_SIMPLEX,
    fontScale=scale,
    thickness=2,
)
print(text_size)
text_w, text_h = text_size
cy = text_h - baseline
print(f'text_w: {text_w}, text_h: {text_h}, baseline: {baseline}, cy: {cy}')
offset_x, offset_y = 50, 30
text_x, text_y = w - text_w - offset_x, h - offset_y
cv2.putText(
    img,
    "Birds".upper(),
    (text_x, text_y),
    cv2.FONT_HERSHEY_SIMPLEX,
    scale,
    (0, 0, 255),
    thickness=2,
)
cv2.rectangle(
    img,
    (text_x, text_y),
    (text_x + text_w, text_y - text_h),
    (255, 255, 255),
    2,
)
cv2.circle(img, (img.shape[1] // 2, img.shape[0] // 2), 50, (255, 0, 0), 5)
cv2.arrowedLine(
    img,
    (0, 0),
    (img.shape[1] // 2, img.shape[0] // 2),
    (255, 255, 0),
    10,
)
cv2.drawMarker(
    img,
    (img.shape[1] // 2, img.shape[0] // 2),
    (0, 0, 255),
    cv2.MARKER_SQUARE,
    10,
)

text = "Funny text"
fontScale = 2
thickness = 3
size, baseline = cv2.getTextSize(
    text,
    cv2.FONT_HERSHEY_SIMPLEX,
    fontScale,
    thickness,
)
baseline += thickness
baseline = 0
text_position = int((w - size[0]) / 2), int((h + size[1]) / 4)
cv2.rectangle(
    img,
    (text_position[0], text_position[1] + baseline),
    (text_position[0] + size[0], text_position[1] - size[1]),
    (255, 255, 255),
    cv2.FILLED,
)
cv2.line(
    img,
    (text_position[0], text_position[1] + thickness),
    (text_position[0] + size[0], text_position[1] + thickness),
    (255, 0, 0),
    thickness,
)
cv2.putText(
    img,
    text,
    text_position,
    cv2.FONT_HERSHEY_SIMPLEX,
    fontScale,
    (0, 0, 255),
    thickness,
)

cv2.imshow("img", img)

cv2.waitKey(0)
