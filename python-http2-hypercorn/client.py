import hashlib
import io
import json
import sys
import time

import httpx
import humanize

host = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


ANSI_CLEAR_LINE = "\033[K"


class IO(io.BytesIO):
    def __init__(self, *args, **kwargs):
        self.n = 0
        self.i = 0
        self.started_at = time.monotonic()
        super().__init__(*args, **kwargs)

    def read(self, size=-1):
        data = super().read(size)
        self.n += len(data)
        print(
            f"{self.n}: {len(data)=} {self.i}\r",
            end="",
            flush=True,
            file=sys.stderr,
        )
        if len(data) == 0:
            elapsed = time.monotonic() - self.started_at
            throughput = humanize.naturalsize(self.n / elapsed)
            print(
                f"{self.n} bytes read in {elapsed:.2f} seconds "
                f"({throughput=}){ANSI_CLEAR_LINE}",
                ANSI_CLEAR_LINE,
                file=sys.stderr,
            )
        self.i += 1
        return data


if __name__ == "__main__":
    client = httpx.Client(http2=False)

    response = client.get(host + "/health")
    response.raise_for_status()
    print(response.text, file=sys.stderr)
    print(response.http_version, file=sys.stderr)

    data = ("0" * 1000 * 1000 * 80).encode()
    sha1 = hashlib.sha1(data).hexdigest()
    buf = IO(data)

    started = time.monotonic()

    response = client.post(
        host + "/upload/",
        files=[
            (
                "metadata",
                (
                    "metadata",
                    json.dumps({"metadata": "-metadata-", "sha1": sha1}),
                    "application/json",
                ),
            ),
            ("raw", ("raw", buf, "application/octet-stream")),
        ],
    )
    elapsed = time.monotonic() - started
    throughput = humanize.naturalsize(len(data) / elapsed)
    print(f"{response.status_code=} {throughput=}", file=sys.stderr)
    print(response.text)
