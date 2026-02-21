from io import BytesIO
from pathlib import Path

import av

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")


class VideoDecoder:
    def __init__(self, config: bytes):
        extradata = _annex_b_to_avcc_extradata(config)

        codec = av.codec.Codec("h264", "r")
        self._ctx = av.codec.CodecContext.create(codec)
        self._ctx.extradata = extradata
        self._ctx.pix_fmt = "yuv420p"
        self._ctx.width = 1080
        self._ctx.height = 1920
        self._ctx.open()

        self._frames: list[bytes] = []
        self._flushed = False

    def first_chunk(self, video: bytes) -> None:
        print("feeding first chunk (MP4 container)", len(video), "bytes")
        # feed the initial MP4 container chunk
        container = av.open(BytesIO(video))
        for packet in container.demux(container.streams.video[0]):
            if packet.size == 0:
                continue
            raw_packet = av.Packet(bytes(packet))
            raw_packet.time_base = packet.time_base
            self._decode_packet(raw_packet)
        container.close()

    def next_chunk(self, video: bytes) -> None:
        print("feeding next chunk (raw H.264)", len(video), "bytes")
        # feed a raw H.264 NAL unit chunk
        packet = av.Packet(video)
        self._decode_packet(packet)

    def frames(self) -> list[bytes]:
        print("flushing decoder and returning frames")
        # flush the decoder (once) and return all accumulated frames as PNGs
        if not self._flushed:
            self._flushed = True
            for frame in self._ctx.decode():
                self._save_frame(frame)
        return self._frames

    def _decode_packet(self, packet: av.Packet) -> None:
        for frame in self._ctx.decode(packet):
            self._save_frame(frame)

    def _save_frame(self, frame: av.VideoFrame) -> None:
        buf = BytesIO()
        frame.to_image().save(buf, format="PNG")
        self._frames.append(buf.getvalue())


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    config = (INPUT_DIR / "enrollment_frame_codec_config.h264").read_bytes()
    decoder = VideoDecoder(config)

    # feed the MP4 container as the first chunk
    decoder.first_chunk((INPUT_DIR / "enrollment_encoded.mp4").read_bytes())

    # feed raw H.264 chunks one by one
    for i in range(9):
        chunk = (INPUT_DIR / f"enrollment_frame_{i}.h264").read_bytes()
        decoder.next_chunk(chunk)

    for i, png_data in enumerate(decoder.frames()):
        out_path = OUTPUT_DIR / f"frame_{i:04d}.png"
        out_path.write_bytes(png_data)
        print(f"saved {out_path}")

    print(f"extracted {len(decoder.frames())} frames to {OUTPUT_DIR}/")


def _annex_b_to_avcc_extradata(data: bytes) -> bytes:
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


if __name__ == "__main__":
    main()
