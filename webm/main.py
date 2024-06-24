import sys
from typing import cast

import av
from PIL import Image

file = sys.argv[1]
print("file:", file)

container = av.open(file)

for i, frame in enumerate(container.decode(video=0), start=1):
    frame_np = cast(av.VideoFrame, frame).to_ndarray(format="bgr24")
    print(i, frame_np.shape)
    Image.fromarray(frame_np).save(f"frame_{i}.png")
