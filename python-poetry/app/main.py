import os
import pathlib

import httpx


def main():
    ip = httpx.get("https://api.ipify.org").text
    print(ip)


print(os.getcwd())
print(pathlib.Path(__file__).parent)

if __name__ == "__main__":
    main()
