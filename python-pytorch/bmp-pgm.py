from PIL import Image

def bmp_to_pgm(bmp_file, pgm_file):
    try:
        img = Image.open(bmp_file)

        if img.mode != 'L':
            img = img.convert('L')

        img.save(pgm_file, format='PPM', mode='L') 

        print(f"PGM image saved as {pgm_file}")

    except Exception as e:
        print(f"rrror during conversion: {e}")

bmp_file_path = "rk86_font.bmp"
pgm_file_path = "rk86_font.pgm"
bmp_to_pgm(bmp_file_path, pgm_file_path)
