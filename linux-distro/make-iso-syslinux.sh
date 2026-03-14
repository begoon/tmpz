#!/usr/bin/env bash
set -euo pipefail

KERNEL="$1"
INITRD="$2"
OUTISO="$3"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

ROOT="$WORKDIR/iso"
mkdir -p "$ROOT/isolinux"

cp "$KERNEL" "$ROOT/bzImage"
cp "$INITRD" "$ROOT/initrd"

cp /usr/lib/ISOLINUX/isolinux.bin "$ROOT/isolinux/"
cp /usr/lib/syslinux/modules/bios/ldlinux.c32 "$ROOT/isolinux/"

cat > "$ROOT/isolinux/isolinux.cfg" <<'EOF'
DEFAULT linux
PROMPT 0
TIMEOUT 1

LABEL linux
    KERNEL /bzImage
    APPEND initrd=/initrd console=ttyS0,115200n8
EOF

xorriso -as mkisofs \
  -o "$OUTISO" \
  -b isolinux/isolinux.bin \
  -c isolinux/boot.cat \
  -no-emul-boot \
  -boot-load-size 4 \
  -boot-info-table \
  "$ROOT"

echo "Created $OUTISO"
