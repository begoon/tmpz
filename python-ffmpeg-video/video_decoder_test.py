from pathlib import Path

from video_decoder import (  # VideoDemuxWithoutConfigurationDecoder,
    VideoDemuxDecoder,
    VideoDemuxDirectDecoder,
    VideoFileDecoder,
    VideoStreamDecoder,
)

INPUT = Path("input")
OUTPUT = Path("output")

CONFIG = (INPUT / "enrollment_frame_codec_config.h264").read_bytes()
MP4 = (INPUT / "enrollment_encoded.mp4").read_bytes()

CHUNKS = (
    ("enrollment_frame_0.h264", 975468, "frame_0000.png"),
    ("enrollment_frame_1.h264", 1086954, "frame_0001.png"),
    ("enrollment_frame_2.h264", 1119764, "frame_0002.png"),
    ("enrollment_frame_3.h264", 1119349, "frame_0003.png"),
    ("enrollment_frame_4.h264", 1061698, "frame_0004.png"),
    ("enrollment_frame_5.h264", 1091196, "frame_0005.png"),
    ("enrollment_frame_6.h264", 1035126, "frame_0006.png"),
    ("enrollment_frame_7.h264", 1117634, "frame_0007.png"),
    ("enrollment_frame_8.h264", 1130136, "frame_0008.png"),
)


def test_demux_decoder() -> None:
    decoder = VideoDemuxDecoder()
    assert decoder is not None

    decoder.configure(CONFIG)

    images = decoder.decode(MP4)
    assert len(images) == len(
        CHUNKS
    ), f"unexpected {len(images)=} != {len(CHUNKS)=}"

    for n, (chunk, frame) in enumerate(zip(CHUNKS, images)):
        assert len(frame) > 0
        sz = chunk[1]
        assert len(frame) == sz, f"unexpected {len(frame)=} != {sz=}"
        assert frame.startswith(b"\x89PNG"), f"unexpected {frame[:16]=}"


def test_demux_without_configuration_decoder() -> None:
    decoder = VideoDemuxDecoder()
    assert decoder is not None

    images = decoder.decode(MP4)
    assert len(images) == len(
        CHUNKS
    ), f"unexpected {len(images)=} != {len(CHUNKS)=}"

    for n, (chunk, frame) in enumerate(zip(CHUNKS, images)):
        assert len(frame) > 0
        sz = chunk[1]
        assert len(frame) == sz, f"unexpected {len(frame)=} != {sz=}"
        assert frame.startswith(b"\x89PNG"), f"unexpected {frame[:16]=}"


def test_demux_direct_without_configuration_decoder() -> None:
    decoder = VideoDemuxDirectDecoder()
    assert decoder is not None

    images = decoder.decode(MP4)
    assert len(images) == len(
        CHUNKS
    ), f"unexpected {len(images)=} != {len(CHUNKS)=}"

    for n, (chunk, frame) in enumerate(zip(CHUNKS, images)):
        assert len(frame) > 0
        sz = chunk[1]
        assert len(frame) == sz, f"unexpected {len(frame)=} != {sz=}"
        assert frame.startswith(b"\x89PNG"), f"unexpected {frame[:16]=}"


def test_file_decoder() -> None:
    decoder = VideoFileDecoder()
    assert decoder is not None

    images = decoder.decode(MP4)
    assert len(images) == len(
        CHUNKS
    ), f"unexpected {len(images)=} != {len(CHUNKS)=}"

    for n, (chunk, frame) in enumerate(zip(CHUNKS, images)):
        assert len(frame) > 0
        sz = chunk[1]
        assert len(frame) == sz, f"unexpected {len(frame)=} != {sz=}"
        assert frame.startswith(b"\x89PNG"), f"unexpected {frame[:16]=}"


def test_video_decoder() -> None:
    decoder = VideoStreamDecoder()
    assert decoder is not None

    decoder.configure(CONFIG)

    for n, (filename, sz, image_file) in enumerate(CHUNKS):
        frame = (INPUT / filename).read_bytes()
        frames = decoder.feed(frame)
        assert frames
        assert len(frames) == 1, f"unexpected {len(frames)=} for chunk {n}"
        frame = frames[0]
        assert len(frame) > 0
        assert len(frame) == sz, f"unexpected {len(frame)=} != {sz=}"
        assert frame.startswith(b"\x89PNG"), f"unexpected {frame[:16]=}"

        expected_image = (OUTPUT / image_file).read_bytes()
        assert (
            frame == expected_image
        ), f"unexpected {frame[:16]=} != {expected_image[:16]=}"
