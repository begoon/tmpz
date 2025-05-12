import os
import time  # type: ignore

import machine  # type: ignore
import network  # type: ignore
import urequests  # type: ignore
from machine import Pin, Timer  # type: ignore

import settings

print(os.uname())

WIFI_SSID = settings.WIFI_SSID
WIFI_PASSWORD = settings.WIFI_PASSWORD

API_URL = "https://api.ipify.org"

wlan = network.WLAN(network.STA_IF)


def connect_wifi():
    if wlan.isconnected():
        print("already connected to WIFI")
        print("local IP:", wlan.ifconfig()[0])
        return True

    print(f"connecting to WIFI network: {WIFI_SSID}...")
    print(wlan.ifconfig())

    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    max_wait_s = 20
    start_time = time.ticks_ms()

    led = Pin("LED", Pin.OUT)

    timer = Timer()

    timer.init(period=100, mode=Timer.PERIODIC, callback=lambda v: led.toggle())

    def timeout():
        return time.ticks_diff(time.ticks_ms(), start_time) < max_wait_s * 1000

    spinner = "\\|/-"
    try:
        while not wlan.isconnected() and timeout():
            status = wlan.status()
            if status == network.STAT_CONNECTING:
                ch, *spinner = spinner
                spinner.append(ch)
                print(f"\r{ch}", end="")
            elif status == network.STAT_WRONG_PASSWORD:
                print("\nerror: wrong wifi password")
                return False
            elif status == network.STAT_NO_AP_FOUND:
                print("\nerror: SSID not found")
                return False
            elif status == network.STAT_CONNECT_FAIL:
                print("\nerror: connection failed (reason unknown)")
                return False
            # status codes:
            # 0=idle, 1=connecting, 2=wrong pwd, 3=connected, <0=error
            elif status < 0 or status >= 3:
                break
            machine.idle()
    finally:
        timer.deinit()
        led.off()

    print("\r")
    if wlan.isconnected():
        print("WIFI connected successfully")
        print("local IP:", wlan.ifconfig()[0])
        return True
    else:
        status = wlan.status()
        print(f"failed to connect to WIFI: {status}")
        wlan.active(False)
        return False


if connect_wifi():
    print(f"connecting to {API_URL}...")
    response = None
    try:
        response = urequests.get(API_URL)

        if response.status_code == 200:
            public_ip = response.text
            print("-" * 20)
            print(f"retrieved public IP: {public_ip}")
            print("-" * 20)
        else:
            print(f"error: {response.status_code} / {response.text}")

    except OSError as e:
        print(f"os error: {e}")
    except Exception as e:
        print(f"unexpected error: {e}")

    finally:
        if response:
            response.close()
            print("response closed")

    print("disconnecting WIFI...")
    wlan.disconnect()
    wlan.active(False)
    print("WIFI disconnected")

else:
    print("cannot proceed without a WIFI connection")
