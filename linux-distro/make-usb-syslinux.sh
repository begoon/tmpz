#!/usr/bin/env bash
set -e

KERNEL="$1"
INITRD="$2"
IMAGE="$3"

SIZE_MB=3
mkdir -p mnt

echo "Creating image..."
dd if=/dev/zero of="$IMAGE" bs=1M count=$SIZE_MB

echo "Partitioning..."
printf 'label: dos\nstart=2048, type=83, bootable\n' | sudo sfdisk "$IMAGE"

sudo modprobe loop
LOOP=$(sudo losetup --show -Pf "$IMAGE")
PART=${LOOP}p1

echo "Formatting..."
sudo mkfs.ext2 "$PART"

sudo mount "$PART" mnt

echo "Installing extlinux..."
sudo mkdir -p mnt/boot/syslinux
sudo extlinux --install mnt/boot/syslinux

echo "Installing MBR..."
sudo dd if=/usr/lib/syslinux/mbr/mbr.bin of="$LOOP"

echo "Copying kernel..."
sudo cp "$KERNEL" mnt/boot/vmlinuz
sudo cp "$INITRD" mnt/boot/initrd

sudo tee mnt/boot/syslinux/syslinux.cfg > /dev/null <<EOF
DEFAULT linux
PROMPT 0
TIMEOUT 0

LABEL linux
    LINUX /boot/vmlinuz
    INITRD /boot/initrd
    APPEND console=ttyS0,115200
EOF

sync
sudo umount mnt
sudo losetup -d "$LOOP"

echo "Created $IMAGE"
