import hashlib
import json
import os
import time

import humanize
from fastapi import FastAPI, Request, UploadFile
from pydantic import BaseModel

application = FastAPI()


@application.get("/")
def index(request: Request):
    print(request.method, request.url.path)
    return dict(os.environ)


@application.get("/health")
def health(request: Request):
    print(request.method, request.url.path)
    return {"version": "0.0.0"}


class Metadata(BaseModel):
    metadata: str
    sha1: str


@application.post("/upload/")
async def upload(request: Request, metadata: UploadFile, raw: UploadFile):
    print(request.method, request.url.path, request.http_version)
    metadata_ = Metadata(**json.load(metadata.file))

    started = time.monotonic()

    contents = await raw.read()
    sha1 = hashlib.sha1(contents).hexdigest()

    elapsed = time.monotonic() - started
    throughput = humanize.naturalsize(len(contents) / elapsed)

    print(f"{len(contents)=} {sha1=} {elapsed=:.2f}s {throughput=}")

    return {
        "metadata": metadata_.model_dump(),
        "filename": raw.filename,
        "sha1": {"received": metadata_.sha1, "computed": sha1},
        "match": metadata_.sha1 == sha1,
        "elapsed": elapsed,
        "size": len(contents),
        "throughput": throughput,
    }
