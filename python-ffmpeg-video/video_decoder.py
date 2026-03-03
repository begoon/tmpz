import io
from io import BytesIO
from typing import cast

import av
from av import codec as avcodec
from av.container import InputContainer
from av.video.codeccontext import VideoCodecContext
from PIL import Image

import slog

logger = slog.get_logger()


class VideoFileDecoder:
    def decode(self, video: bytes) -> list[bytes]:
        logger.info("decode video", sz=len(video))

        frames: list[bytes] = []
        with av.open(io.BytesIO(video)) as container:
            assert isinstance(
                container, InputContainer
            ), f"invalid {type(container)=}"

            streams = [v for v in container.streams if v.type == "video"]
            assert streams, "video streams not found in the container"

            stream = streams[0]
            for frame in container.decode(stream):
                assert isinstance(
                    frame, av.VideoFrame
                ), f"invalid {type(frame)=}"
                frames.append(png(frame))

        return frames


class VideoDemuxDecoder:
    def __init__(self) -> None:
        self._ctx: VideoCodecContext | None = None

    def configure(self, config: bytes) -> None:
        extradata = annex_b_to_avcc_extradata(config)

        codec = avcodec.Codec("h264", "r")
        assert codec.type == "video", f"invalid {codec.type=}"
        assert isinstance(codec, avcodec.Codec), f"invalid {type(codec)=}"
        assert codec.is_decoder

        self._ctx = cast(VideoCodecContext, avcodec.CodecContext.create(codec))
        self._ctx.extradata = extradata
        self._ctx.pix_fmt = "yuv420p"
        self._ctx.width = 1080
        self._ctx.height = 1920

    def decode(self, video: bytes) -> list[bytes]:
        logger.info("decode video", sz=len(video))

        frames: list[bytes] = []

        container = av.open(BytesIO(video))
        assert isinstance(
            container, InputContainer
        ), f"invalid {type(container)=}"

        if self._ctx is None:
            streams = [v for v in container.streams if v.type == "video"]
            assert streams, "video streams not found in the container"

            stream = container.streams.video[0]

            ctx = avcodec.CodecContext.create(stream.codec_context.codec)
            assert isinstance(ctx, VideoCodecContext), f"invalid {type(ctx)=}"

            self._ctx = ctx
            self._ctx.extradata = stream.codec_context.extradata
            self._ctx.width = stream.codec_context.width
            self._ctx.height = stream.codec_context.height

        self._ctx.open()

        for packet in container.demux(container.streams.video[0]):
            if packet.size == 0:
                continue
            for frame in self._ctx.decode(packet):
                frames.append(png(frame))

        for frame in self._ctx.decode():
            frames.append(png(frame))

        container.close()
        return frames


class VideoDemuxDirectDecoder:
    def decode(self, video: bytes) -> list[bytes]:
        frames: list[bytes] = []

        with av.open(BytesIO(video)) as container:
            streams = [v for v in container.streams if v.type == "video"]
            assert streams, "video streams not found in the container"

            assert isinstance(
                container, InputContainer
            ), f"invalid {type(container)=}"
            stream = container.streams.video[0]

            ctx = stream.codec_context

            for packet in container.demux(stream):
                if packet.size == 0:
                    continue
                for frame in ctx.decode(packet):
                    frames.append(png(frame))

            for frame in ctx.decode():
                frames.append(png(frame))

        return frames


class VideoStreamDecoder:
    def __init__(self) -> None:
        self._ctx: VideoCodecContext | None = None

    @property
    def ctx(self) -> VideoCodecContext:
        assert self._ctx is not None, "context: decoder not configured"
        return self._ctx

    def configure(self, config: bytes) -> None:
        extradata = annex_b_to_avcc_extradata(config)

        codec = avcodec.Codec("h264", "r")
        assert codec.type == "video", f"invalid {codec.type=}"
        assert isinstance(codec, avcodec.Codec), f"invalid {type(codec)=}"
        assert codec.is_decoder

        self._ctx = cast(VideoCodecContext, avcodec.CodecContext.create(codec))
        self._ctx.extradata = extradata
        self._ctx.pix_fmt = "yuv420p"
        self._ctx.width = 1080
        self._ctx.height = 1920

        self.ctx.open()

    def feed(self, video: bytes) -> list[bytes]:
        logger.info("feed chunk (raw H.264)", sz=len(video))
        packet = av.Packet(video)
        return [png(f) for f in self.ctx.decode(packet)]

    def flush(self) -> list[bytes]:
        logger.info("flush decoder")
        return [png(f) for f in self.ctx.decode()]


def png(frame: av.VideoFrame) -> bytes:
    buf = BytesIO()
    image: Image.Image = frame.to_image()  # type: ignore[no-untyped-call]
    image.save(buf, format="PNG")
    return buf.getvalue()


def annex_b_to_avcc_extradata(data: bytes) -> bytes:
    """
    Parse Annex B bytestream (with 00 00 00 01 start codes)
    into AVCC extradata.
    """
    nalus = []
    i = 0
    while i < len(data):
        if data[i : i + 4] == b"\x00\x00\x00\x01":
            i += 4
            end = data.find(b"\x00\x00\x00\x01", i)
            if end == -1:
                end = len(data)
            nalus.append(data[i:end])
            i = end
        else:
            i += 1

    sps_list = [n for n in nalus if (n[0] & 0x1F) == 7]
    pps_list = [n for n in nalus if (n[0] & 0x1F) == 8]

    assert sps_list, "could not find SPS in codec config"
    assert pps_list, "could not find PPS in codec config"

    sps = sps_list[0]
    pps = pps_list[0]

    result = bytearray()
    result.append(1)  # version
    result.append(sps[1])  # profile
    result.append(sps[2])  # compatibility
    result.append(sps[3])  # level
    result.append(0xFF)  # NALU length size = 4
    result.append(0xE1)  # 1 SPS
    result.extend(len(sps).to_bytes(2, "big"))
    result.extend(sps)
    result.append(1)  # 1 PPS
    result.extend(len(pps).to_bytes(2, "big"))
    result.extend(pps)
    return bytes(result)
