import socket
from contextlib import contextmanager

import docker
from pymongo import MongoClient
from tenacity import retry, stop_after_delay, wait_fixed


@contextmanager
def MongoRunner():
    client = docker.from_env()

    def available_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    @retry(stop=stop_after_delay(30), wait=wait_fixed(0.5))
    def wait(port: int):
        uri = f"mongodb://127.0.0.1:{port}"
        client = MongoClient(uri, serverSelectionTimeoutMS=1000)
        try:
            client.admin.command("ping")
        finally:
            client.close()

    port = available_port()
    container = client.containers.run(
        "mongo:latest",
        command="mongod --dbpath /data/db",
        ports={"27017/tcp": port},
        remove=True,
        detach=True,
        tmpfs={"/data/db": "rw,size=1024m"},
    )
    try:
        wait(port)
        location = f"127.0.0.1:{port}"
        print("mongodb is ready at", location)
        yield location
    finally:
        container.stop()
        print("mongodb stopped")


def main():
    with MongoRunner() as addr:
        client = MongoClient(f"mongodb://{addr}")
        try:
            print("mongodb version:", client.server_info()["version"])
        finally:
            client.close()


if __name__ == "__main__":
    main()
