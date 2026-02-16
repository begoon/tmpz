import time
from typing import Sequence

from google.cloud import storage


def compose_gcs_objects(
    bucket_name: str,
    source_names: Sequence[str],
    destination_name: str,
    *,
    client: storage.Client | None = None,
    destination_content_type: str | None = None,
) -> None:
    assert source_names, "source_names is empty"

    max_components: int = 32
    cleanup_intermediates = True
    temp_prefix = f"{destination_name.rstrip('/')}.compose-buffer"

    client = client or storage.Client()
    bucket = client.bucket(bucket_name)

    intermediates: list[str] = []

    current_level = list(source_names)
    level = 0

    while len(current_level) > 1:
        next_level: list[str] = []
        group = range(0, len(current_level), max_components)

        for index, start in enumerate(group):
            group_names = current_level[start : start + max_components]

            intermediate_name = (
                f"{temp_prefix.rstrip('/')}/"
                f"{destination_name.strip('/').replace('/', '_')}"
                f".level{level:02d}.group{index:05d}"
            )
            print(
                f"{level=}: #{index} | compose {len(group_names):0>2} "
                f"objects -> {intermediate_name}"
            )

            if len(group_names) == 1:
                next_level.append(group_names[0])
                continue

            group_blobs = [bucket.blob(name) for name in group_names]
            intermediate_blob = bucket.blob(intermediate_name)

            intermediate_blob.compose(group_blobs)

            intermediates.append(intermediate_name)
            next_level.append(intermediate_name)

        current_level = next_level
        level += 1

    assert len(current_level) == 1, "1 object should remain"
    final_source_name = current_level[0]

    if final_source_name != destination_name:
        print(f"finalise: {final_source_name} -> {destination_name}")
        source = bucket.blob(final_source_name)
        destination = bucket.blob(destination_name)

        bucket.copy_blob(source, bucket, new_name=destination_name)

        if destination_content_type is not None:
            destination.content_type = destination_content_type
            destination.patch()

    if cleanup_intermediates and intermediates:
        for name in intermediates:
            # prevent accidental deletion of final destination
            if name != destination_name:
                try:
                    bucket.blob(name).delete()
                except Exception as e:
                    print(f"failed to delete intermediate {name=}: {e}")


if __name__ == "__main__":
    location = "xyz"
    chunks = [f"{location}/chunks/chunk-{i:03d}.bin" for i in range(0, 100)]
    started = time.monotonic()
    result = compose_gcs_objects(
        bucket_name="test-binding",
        source_names=chunks,
        destination_name=f"{location}/jumbo.bin",
        destination_content_type="application/octet-stream",
    )
    elapsed = time.monotonic() - started
    print(f"{elapsed:.2f} seconds")
