import sys  # type: ignore

import framebuf  # type: ignore
import utime  # type: ignore
from machine import I2C, Pin  # type: ignore

from ssd1306 import SSD1306_I2C

pix_res_x = 128
pix_res_y = 64


def init_i2c(device, scl_pin, sda_pin):
    i2c_dev = I2C(device, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=200000)
    i2c_addr = [hex(i) for i in i2c_dev.scan()]

    if not i2c_addr:
        print("No I2C Display Found")
        sys.exit()
    else:
        print("I2C Address      : {}".format(i2c_addr[0]))
        print("I2C Configuration: {}".format(i2c_dev))

    return i2c_dev


rpi_bitmap_32x32 = [
    "000000000000000000000000000000",
    "00000000000000000000000000000000",
    "00000000000000000000000000000000",
    "00000000011111000011111100000000",
    "00000001100001100100000010000000",
    "00000001000000011000000010000000",
    "00000001000100011000100010000000",
    "00000001000001011010000010000000",
    "00000000100000111100000100000000",
    "00000000010000111110001100000000",
    "00000000011111101111110000000000",
    "00000000010011000010011100000000",
    "00000000100111000001000100000000",
    "00000000101111111111110100000000",
    "00000000111000011000011100000000",
    "00000001110000011000001110000000",
    "00000010010000011000001001000000",
    "00000010010000011000001001000000",
    "00000010110000011100001001000000",
    "00000010111101100011111011000000",
    "00000001111111000011110110000000",
    "00000001000110000001100010000000",
    "00000001100010000001000010000000",
    "00000000100011000010000100000000",
    "00000000100001111111000100000000",
    "00000000011111111111011000000000",
    "00000000001110000001110000000000",
    "00000000000011000010000000000000",
    "00000000000000111100000000000000",
    "00000000000000000000000000000000",
    "00000000000000000000000000000000",
    "00000000000000000000000000000000",
]

rpi_bitmap = bytearray(
    int(line[i : i + 8], 2)
    for line in rpi_bitmap_32x32
    for i in range(0, 32, 8)
)


def display_logo(oled):
    fb = framebuf.FrameBuffer(rpi_bitmap, 32, 32, framebuf.MONO_HLSB)

    oled.fill(0)
    oled.blit(fb, 96, 0)
    oled.show()


def display_text(oled):
    oled.text("Raspberry Pi", 5, 5)
    oled.text("Pico", 5, 15)
    oled.text("Innovation", 5, 25)
    oled.text("2025", 5, 35)
    oled.show()


start_time = utime.ticks_ms()


def display_animation(oled):
    for _ in range(10 * 5):
        elapsed_time = (
            utime.ticks_diff(utime.ticks_ms(), start_time) // 1000
        ) + 1

        oled.fill_rect(5, 50, oled.width - 5, 8, 0)

        oled.text(str(elapsed_time) + " sec", 5, 50)
        oled.show()
        utime.sleep_ms(200)
        oled.scroll(1, 1)


def main():
    i2c_dev = init_i2c(device=1, scl_pin=27, sda_pin=26)
    oled = SSD1306_I2C(pix_res_x, pix_res_y, i2c_dev)
    oled.invert(1)

    while True:
        display_logo(oled)
        display_text(oled)
        display_animation(oled)


if __name__ == "__main__":
    main()
