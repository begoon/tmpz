#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Building inside Docker ==="
docker build --platform linux/amd64 -t linux-distro-builder .

echo "=== Extracting bzImage and init.cpio ==="
container=$(docker create --platform linux/amd64 linux-distro-builder)
docker cp "$container:/build/bzImage" ./bzImage
docker cp "$container:/build/init.cpio" ./init.cpio
docker rm "$container" > /dev/null

echo "=== Done ==="
ls -lh bzImage init.cpio

echo ""
echo "Run with:"
echo "  qemu-system-x86_64 -kernel bzImage -initrd init.cpio -append \"console=ttyS0 rdinit=/init\" -nographic"
