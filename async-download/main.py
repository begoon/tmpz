import asyncio
import random
import time

import httpx

size = 10
link = f"http://ipv4.download.thinkbroadband.com/{size}MB.zip"
N = 10


async def download_file(
    client: httpx.AsyncClient,
    url: str,
    n: int,
) -> [int, int]:
    print(f"downloading {url}")
    if random.random() < 0.2:
        raise Exception(f"random exception: {n=}")
    await asyncio.sleep(1 * random.random())
    response = await client.get(url)
    sz = len(response.content)
    print(f"{n}: downloaded {url}, {sz} bytes")
    expected = size * 1024 * 1024
    assert sz == expected, f"unexpected size {sz}, expected {expected}"
    return [sz, n]


async def main():
    start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        tasks = [download_file(client, link, i) for i in range(N)]
        result = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.perf_counter() - start
        print(result)
        result = [x for x in result if not isinstance(x, Exception)]
        result = [x[0] for x in result]
        downloaded = sum(result) / 1024 / 1024

        print(f"{N} files downloaded in {duration:0.2f} seconds")
        print("throughput {:0.2f} MB/s".format(downloaded / duration))


if __name__ == "__main__":
    asyncio.run(main())
