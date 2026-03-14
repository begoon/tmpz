# CLAUDE.md

## Project Overview

Minimal Linux distribution built from scratch. Boots a custom Linux kernel with a tiny initramfs containing a single `/init` binary that prints "Aloha!" and loops forever. Supports both C and Go implementations of init. The entire system is ~1.2 MB.

## Tech Stack

- **Kernel**: Linux 6.19.6 built with `tinyconfig` + custom fragment
- **Init**: C (`main.c`) or Go (`main.go`), statically compiled
- **Build runner**: `just` (Justfile)
- **Bootloaders**: GRUB and syslinux/isolinux
- **Testing**: QEMU (`qemu-system-x86_64`)

## Project Structure

```
main.c / main.go          # Init program (prints "Aloha!" then loops)
Justfile                   # Build recipes
make-iso-grub.sh           # Create ISO with GRUB bootloader
make-iso-syslinux.sh       # Create ISO with syslinux (verbose boot)
make-iso-syslinux-quiet.sh # Create ISO with syslinux (quiet boot)
make-usb-syslinux.sh       # Create bootable USB image with syslinux
README.md                  # Detailed build instructions and kernel config
```

### Generated artifacts (gitignored)

- `fs/` — initramfs root directory containing the compiled `/init` binary
- `bzImage` — compiled Linux kernel
- `init.cpio.lzma` — LZMA-compressed cpio initramfs archive
- `os.iso` — bootable ISO image
- `usb.img` — bootable USB disk image

## Build Commands

```bash
# Build init binary (choose one)
just build-c          # C version: gcc --static main.c -o fs/init
just build-go         # Go version: CGO_ENABLED=0 static binary

# Create initramfs archive
just initramfs        # builds init + creates fs/ → init.cpio.lzma

# Create bootable images (args: bzImage initramfs output)
./make-iso-grub.sh ./bzImage ./init.cpio.lzma os.iso
./make-iso-syslinux.sh ./bzImage ./init.cpio.lzma os.iso
./make-iso-syslinux-quiet.sh ./bzImage ./init.cpio.lzma os.iso
./make-usb-syslinux.sh ./bzImage ./init.cpio.lzma usb.img

# Clean
just clean
```

## Running with QEMU

```bash
# Direct kernel boot (fastest for development)
qemu-system-x86_64 -kernel bzImage -initrd init.cpio.lzma \
    -append "rdinit=/init console=ttyS0,115200n8" -nographic -serial mon:stdio

# Boot from ISO
qemu-system-x86_64 -cdrom os.iso -nographic -serial mon:stdio

# Boot from USB image
qemu-system-x86_64 -drive file=usb.img,format=raw -nographic -serial mon:stdio
```

Exit QEMU: `Ctrl+A` then `X`.

## Kernel Configuration

The kernel starts from `tinyconfig` and adds these required options:

| Config | Purpose |
|--------|---------|
| `CONFIG_BLK_DEV_INITRD=y` | Initramfs support |
| `CONFIG_RD_LZMA=y` | LZMA decompression for initrd |
| `CONFIG_BINFMT_ELF=y` | Run ELF binaries |
| `CONFIG_PRINTK=y` | Kernel logging |
| `CONFIG_TTY=y`, `VT=y`, `VT_CONSOLE=y` | Terminal/console |
| `CONFIG_SERIAL_8250=y`, `SERIAL_8250_CONSOLE=y` | Serial console (for QEMU -nographic) |
| `CONFIG_FUTEX=y`, `POSIX_TIMERS=y`, `HIGH_RES_TIMERS=y`, `EPOLL=y`, `EVENTFD=y` | Required by Go runtime only |

## Key Design Decisions

- **Static binaries only**: C uses `gcc --static`, Go uses `CGO_ENABLED=0` — no libc or shared libraries in initramfs
- **No busybox or shell**: initramfs contains only `/init`, nothing else
- **Serial console**: all boot configs use `console=ttyS0` for headless QEMU testing
- **LZMA compression**: smallest initramfs size at cost of slightly slower decompression

## Shell Scripts

All image-building scripts (`make-*.sh`) take 3 positional args: `<bzImage> <initramfs> <output>`. They create temp directories, assemble the image layout, build the image, then clean up. The USB script requires `sudo` for loop device and extlinux operations.
