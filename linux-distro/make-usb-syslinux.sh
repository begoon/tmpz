#!/usr/bin/env bash
set -euo pipefail

KERNEL="${1:?missing kernel path}"
INITRD="${2:?missing initrd path}"
IMAGE="${3:?missing image path}"

SIZE_KB=2500
MNT_DIR="mnt"
LOOP=""

cleanup() {
    sync || true

    if mountpoint -q "$MNT_DIR"; then
        sudo umount "$MNT_DIR" || true
    fi

    if [[ -n "$LOOP" ]]; then
        sudo losetup -d "$LOOP" || true
    fi
}

trap cleanup EXIT INT TERM

mkdir -p "$MNT_DIR"

echo "Creating image..."
dd if=/dev/zero of="$IMAGE" bs=1024 count="$SIZE_KB"

echo "Partitioning..."
printf 'label: dos\nstart=2048, type=83, bootable\n' | sudo sfdisk "$IMAGE"

sudo modprobe loop
LOOP=$(sudo losetup --show -Pf "$IMAGE")
PART="${LOOP}p1"

echo "Formatting..."
sudo mkfs.ext2 "$PART"

echo "Mounting..."
sudo mount "$PART" "$MNT_DIR"

echo "Installing extlinux..."
sudo mkdir -p "$MNT_DIR/boot/syslinux"
sudo extlinux --install "$MNT_DIR/boot/syslinux"

echo "Installing MBR..."
sudo dd if=/usr/lib/syslinux/mbr/mbr.bin of="$LOOP"

echo "Copying kernel..."
sudo cp "$KERNEL" "$MNT_DIR/boot/vmlinuz"
sudo cp "$INITRD" "$MNT_DIR/boot/initrd"

sudo tee "$MNT_DIR/boot/syslinux/syslinux.cfg" > /dev/null <<EOF
DEFAULT linux
PROMPT 0
TIMEOUT 0

LABEL linux
    LINUX /boot/vmlinuz
    INITRD /boot/initrd
    APPEND console=ttyS0,115200
EOF

echo "Created $IMAGE"
