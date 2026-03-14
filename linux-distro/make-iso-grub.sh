#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./make-iso.sh /path/to/bzImage /path/to/init.cpio output.iso
#
# Example:
#   ./make-iso.sh ./bzImage ./init.cpio myos.iso

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <bzImage> <init.cpio> <output.iso>" >&2
    exit 1
fi

KERNEL="$(realpath "$1")"
INITRD="$(realpath "$2")"
OUTISO="$(realpath "$3")"

for tool in grub-mkrescue xorriso mformat; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Error: required tool '$tool' not found in PATH" >&2
        exit 1
    fi
done

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

ISO_ROOT="$WORKDIR/isodir"
BOOT_DIR="$ISO_ROOT/boot"
GRUB_DIR="$BOOT_DIR/grub"

mkdir -p "$GRUB_DIR"

cp "$KERNEL" "$BOOT_DIR/bzImage"
cp "$INITRD" "$BOOT_DIR/init.cpio"

cat > "$GRUB_DIR/grub.cfg" <<'EOF'
set timeout=0
set default=0

menuentry "boot minimal linux" {
    linux /boot/bzImage console=ttyS0 quiet
    initrd /boot/init.cpio
}
EOF

grub-mkrescue -o "$OUTISO" "$ISO_ROOT"

echo "Created ISO: $OUTISO"
echo
echo "Test in QEMU:"
echo "  qemu-system-x86_64 -cdrom $OUTISO -serial mon:stdio -nographic"
echo
echo "Flash to USB (WARNING: destroys target disk contents):"
echo "  sudo dd if=$OUTISO of=/dev/sdX bs=4M status=progress oflag=sync"
echo
echo "Then boot the machine from that USB stick."
