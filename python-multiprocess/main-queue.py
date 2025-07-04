import hashlib
import multiprocessing
import sys
import time
from multiprocessing import Manager, Process, Queue


def process(task_queue: Queue, result_list: list):
    while True:
        content, filename = task_queue.get()
        if filename is None:
            break
        print("processing", filename, "size", len(content))
        started = time.monotonic()
        for i in range(10000):
            sha1 = hashlib.sha1(content).hexdigest()
        elapsed = time.monotonic() - started
        print(f"sha1({filename}) = {sha1} in {elapsed:.2f} seconds")
        result_list.append((filename, sha1, elapsed))


def load_task_to_queue(task_queue: Queue):
    for i in range(4):
        name = f"image_{i:04X}.raw"
        content = f"{i:04X}" * (1024 * 256)  # 1 MB of data
        task_queue.put((content.encode(), name))


def main():
    N = multiprocessing.cpu_count() if not sys.argv[1:] else int(sys.argv[1])

    print(f"using {N} workers")

    manager = Manager()
    task_queue = manager.Queue()
    results = manager.list()

    load_task_to_queue(task_queue)

    workers = []
    for _ in range(N):
        p = Process(target=process, args=(task_queue, results))
        p.start()
        workers.append(p)

    for _ in range(N):
        task_queue.put((None, None))

    for p in workers:
        p.join()

    for filename, sha1, duration in list(results):
        print(f"{filename}: {sha1} {duration:.2f}s")


if __name__ == "__main__":
    started = time.monotonic()
    main()
    elapsed = time.monotonic() - started
    print(f"total elapsed time: {elapsed:.2f}s")
