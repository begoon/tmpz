#!/usr/bin/env python3
import sys
import time
import urllib.error
import urllib.request


def flag(name: str | tuple[str, ...]) -> bool:
    if isinstance(name, str):
        name = (name,)
    return any(n in sys.argv for n in name)


def arg(name: str, default: str = "") -> str:
    if name not in sys.argv:
        return default

    index = sys.argv.index(name)
    try:
        return sys.argv[index + 1]
    except IndexError:
        return default


def ping(
    url: str,
    timeout: float,
    statuses: tuple[int, ...] | int = 200,
) -> bool:
    if isinstance(statuses, int):
        statuses = (statuses,)
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            code = getattr(response, "status", None) or response.getcode()
            return code in statuses
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def main() -> int:
    def usage() -> int:
        print(
            f"usage: {sys.argv[0]} "
            "--url <url> "
            "[--status_code <code> (default: 200)] "
            "[--timeout <seconds> (default: 60)] "
            "[--interval <seconds> (default: 2)]",
            "[--verbose/-v]",
            file=sys.stderr,
        )
        return 1

    url = arg("--url")
    if not url:
        return usage()

    status_code = int(arg("--status_code", "200"))

    timeout = int(arg("--timeout", "60"))
    interval = int(arg("--interval", "2"))

    verbose = flag(("--verbose", "-v"))

    started = time.monotonic()
    deadline = started + float(timeout)

    print(f"waiting for {url} (status {status_code})")

    attempt = 0
    while True:
        attempt += 1
        ok = ping(url, float(timeout), statuses=status_code)
        if ok:
            elapsed = time.monotonic() - started
            print(f"ready after {elapsed:.2f}s ({url})")
            return 0

        now = time.monotonic()
        if now >= deadline:
            if verbose:
                print(f"timeout after {timeout}s waiting for {url}")
            return 1

        remaining = max(0.0, deadline - now)
        delay = min(float(interval), remaining)
        if verbose:
            print(f"attempt {attempt}: not ready, waiting {delay:.2f}s...")
        time.sleep(delay)


if __name__ == "__main__":
    exit(main())
