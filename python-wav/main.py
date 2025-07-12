import wave

BIT_RATE = 1100
SAMPLE_RATE = 22050
SAMPLES_PER_BIT = SAMPLE_RATE / BIT_RATE
print(f"{SAMPLES_PER_BIT=}")

threshold = 100


def get_bit(data, i):
    v = data[i]
    while i < len(data) and data[i] == v:
        i += 1
    if i >= len(data):
        return [None, i]
    bit = 1 if data[i] >= threshold else 0
    return [bit, i + int(SAMPLES_PER_BIT * 0.75)]


def seek_sync_byte(data, i):
    byte = 0
    while True:
        byte <<= 1
        bit, i = get_bit(data, i)
        if bit is None:
            return [None, i]
        byte = (byte | bit) & 0xFF
        if byte == 0xE6:
            return [byte, i]


def get_byte(data, i):
    byte = 0
    for j in reversed(range(8)):
        bit, i = get_bit(data, i)
        if bit is None:
            return [None, i]
        byte |= bit << j
    print(f"{byte:02X} ", end="")
    return [byte, i]


def decode_frames(frames):
    data = list(frames)

    i = 0

    bit, i = seek_sync_byte(data, i)
    if bit is None:
        print("sync byte (E6) not found")
        return
    print(f"sync byte (E6) found at offset {i - 1:08X}")

    offset = 0
    while True:
        if offset & 0x0F == 0:
            print(f"{offset:08X} ", end="")
        byte, i = get_byte(data, i)
        if byte is None:
            break
        if (offset & 0x07) == 0x07:
            print(" ", end="")
        if (offset & 0x0F) == 0x0F:
            print()
        offset += 1
    print()


def main():
    with wave.open("in.wav", "rb") as f:
        print(f.getparams())
        frames = f.readframes(f.getnframes())
        print(f"read {len(frames)} frames")

        decode_frames(frames)


if __name__ == "__main__":
    main()
