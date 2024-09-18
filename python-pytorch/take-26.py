from pathlib import Path

pgm_file_path = "rk86_font.pgm"

pgm = Path(pgm_file_path).read_bytes()
pgm_sz = len(pgm)

header, wh, depth, data = pgm.split(b'\n', 4)
print(header, wh, depth, len(data), len(data)/8)

peramble_sz = pgm_sz - len(data)
print(peramble_sz)


data_offset_A = 65 * 8 * 8

for i in range(26):
    offset = data_offset_A + i * 8 * 8
    print(f"{chr(i + 65)}/{offset:04X}/{offset+peramble_sz:04X}")
    for j in range(8):
        line_offset = offset + j * 8
        row = ["X" if v else "." for v in data[line_offset:line_offset + 8]]
        print("".join(row))
    print()

alphabet_26_size = 26 * 8 * 8
alphabet_26 = data[data_offset_A:data_offset_A + alphabet_26_size]
print(len(alphabet_26))
Path("alphabet_26.bin").write_bytes(alphabet_26)