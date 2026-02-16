import argparse
import os
from typing import Optional

from google.cloud import storage


def parse_gs_url(gs_url: str) -> tuple[str, str]:
    if not gs_url.startswith("gs://"):
        raise ValueError("expect gs://BUCKET or gs://BUCKET/prefix")
    rest = gs_url[5:]
    parts = rest.split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) == 2 else ""
    prefix = prefix.strip("/")
    return bucket, prefix


def upload_one(
    client: storage.Client,
    bucket_name: str,
    object_name: str,
    total_size: int,
    chunk_size: int,
    content_type: str = "application/octet-stream",
    precondition: Optional[str] = None,
) -> None:
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.content_type = content_type

    blob.chunk_size = chunk_size

    if_generation_match = 0 if precondition == "no-clobber" else None

    remaining = total_size
    with blob.open("wb", if_generation_match=if_generation_match) as f:
        while remaining > 0:
            n = min(chunk_size, remaining)
            f.write(os.urandom(n))
            remaining -= n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dest",
        required=True,
        help="destination like gs://bucket/prefix",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="number of chunks (default 100)",
    )
    parser.add_argument(
        "--size-mb",
        type=int,
        default=100,
        help="size per chunk in MiB (default 100)",
    )
    parser.add_argument(
        "--upload-chunk-mb",
        type=int,
        default=8,
        help="upload write chunk size in MiB (default 8), multiple of 256 KiB",
    )
    parser.add_argument(
        "--no-clobber",
        action="store_true",
        help="fail if an object already exists (uses if_generation_match=0)",
    )
    args = parser.parse_args()

    bucket_name, prefix = parse_gs_url(args.dest)

    total_size = args.size_mb * 1024 * 1024
    chunk_size = args.upload_chunk_mb * 1024 * 1024

    if chunk_size % (256 * 1024) != 0:
        raise ValueError(
            "--upload-chunk-mb must make chunk size a multiple of 256 KiB"
        )

    client = storage.Client()

    for i in range(args.count):
        name = f"chunk-{i:03d}.bin"
        object_name = f"{prefix}/{name}" if prefix else name

        print(
            f"uploading gs://{bucket_name}/{object_name} "
            f"({args.size_mb} MiB)"
        )
        upload_one(
            client=client,
            bucket_name=bucket_name,
            object_name=object_name,
            total_size=total_size,
            chunk_size=chunk_size,
            precondition="no-clobber" if args.no_clobber else None,
        )

    print("done")


if __name__ == "__main__":
    main()
