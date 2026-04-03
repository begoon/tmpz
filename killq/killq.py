#!/usr/bin/env -S uv run --script
import subprocess
import sys

IGNORED_SUBSTRINGS = ["Dropbox", "killq"]
EXECUTE_FLAG = "-X"
NO_PORT_MARKER = "-"


def get_listening_ports_by_pid() -> dict[str, list[str]]:
    try:
        result = subprocess.run(
            ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-F", "pn"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {}

    ports_by_pid: dict[str, list[str]] = {}
    current_pid = None

    for line in result.stdout.splitlines():
        if line.startswith("p"):
            current_pid = line[1:]
            ports_by_pid.setdefault(current_pid, [])
            continue

        if not current_pid or not line.startswith("n"):
            continue

        port = line[1:].rsplit(":", 1)[-1]
        if port not in ports_by_pid[current_pid]:
            ports_by_pid[current_pid].append(port)

    return ports_by_pid


def query_matches(command_line: str, ports: list[str], query: str) -> bool:
    if query in command_line:
        return True

    return any(query in port for port in ports)


def main() -> int:
    if len(sys.argv) < 2:
        print(
            f"Usage: {sys.argv[0]} <search-string| -exclude-string> [<search-string| -exclude-string> ...] [{EXECUTE_FLAG}]",
            file=sys.stderr,
        )
        return 1

    execute_kill = False
    include_queries = []
    exclude_queries = []
    for value in sys.argv[1:]:
        if value == EXECUTE_FLAG:
            execute_kill = True
            continue
        if value.startswith("-"):
            exclude_queries.append(value[1:])
            continue
        include_queries.append(value)

    if not include_queries and not exclude_queries:
        print(
            f"Usage: {sys.argv[0]} <search-string| -exclude-string> [<search-string| -exclude-string> ...] [{EXECUTE_FLAG}]",
            file=sys.stderr,
        )
        return 1

    try:
        result = subprocess.run(
            ["ps", "-axww", "-o", "pid=", "-o", "command="],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Failed to list processes: {exc}", file=sys.stderr)
        return exc.returncode or 1

    ignored_substrings = [value.casefold() for value in IGNORED_SUBSTRINGS]
    listening_ports_by_pid = get_listening_ports_by_pid()
    matched_pids = []

    for process_line in result.stdout.splitlines():
        try:
            pid, command_line = process_line.strip().split(None, 1)
        except ValueError:
            continue

        ports = listening_ports_by_pid.get(pid, [])

        if not all(query_matches(command_line, ports, query) for query in include_queries):
            continue
        if any(query_matches(command_line, ports, query) for query in exclude_queries):
            continue
        command_line_folded = command_line.casefold()
        if any(value in command_line_folded for value in ignored_substrings):
            continue

        port_suffix = ":" + ":".join(ports) if ports else f":{NO_PORT_MARKER}"
        matched_pids.append(pid)
        print(f"{pid} {port_suffix} {command_line}")

    if not execute_kill or not matched_pids:
        return 0

    print(" ".join(matched_pids))
    answer = input("kill -9 (Y/n)? ").strip().casefold()
    if answer not in {"", "y", "yes"}:
        return 0

    exit_code = 0
    for pid in matched_pids:
        print(pid, end="", flush=True)
        try:
            subprocess.run(["kill", "-9", pid], check=True)
        except subprocess.CalledProcessError as exc:
            print()
            print(f"Failed to kill PID {pid}: {exc}", file=sys.stderr)
            exit_code = exc.returncode or 1
            continue
        print()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
