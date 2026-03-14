# Build minimal linux kernel + custom /init bootable system

## main.c

```c
#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    printf("Aloha!\n");
    while (1) sleep(1);
}
```

```sh
gcc --static main.c -o fs/init
```

## main.go

```go
package main

import (
    "fmt"
)

func main() {
    fmt.Println("Aloha!")
    select {}
}
```

```sh
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -a -ldflags="-s -w" -o fs/init main.go
```

## Build linux kernel

```sh
make tinyconfig
```

### Booting initramfs

```text
CONFIG_BLK_DEV_INITRD=y
CONFIG_RD_LZMA=y
```

### Running /init

```text
CONFIG_BINFMT_ELF=y
```

### Seeing output on the screen

```text
CONFIG_PRINTK=y
CONFIG_TTY=y
CONFIG_VT=y
CONFIG_VT_CONSOLE=y
```

### Enable using QEMU with -nographic

```text
CONFIG_SERIAL_8250=y
CONFIG_SERIAL_8250_CONSOLE=y
```

### What the Go runtime specifically needed

```text
CONFIG_FUTEX=y
CONFIG_POSIX_TIMERS=y
CONFIG_HIGH_RES_TIMERS=y
CONFIG_EPOLL=y
CONFIG_EVENTFD=y
```

### Summary (initramfs.fragment)

```text
CONFIG_BLK_DEV_INITRD=y
CONFIG_RD_LZMA=y
CONFIG_BINFMT_ELF=y

CONFIG_PRINTK=y
CONFIG_TTY=y
CONFIG_VT=y
CONFIG_VT_CONSOLE=y

CONFIG_FUTEX=y
CONFIG_POSIX_TIMERS=y
CONFIG_HIGH_RES_TIMERS=y
CONFIG_EPOLL=y
CONFIG_EVENTFD=y

CONFIG_SERIAL_8250=y
CONFIG_SERIAL_8250_CONSOLE=y
```

## Configure the kernel

```sh
curl https://www.kernel.org/pub/linux/kernel/v6.x/linux-6.19.6.tar.xz >linux-6.19.6.tar.xz
tar xf linux-6.19.6.tar.xz
mv linux-6.19.6 linux
cd linux
```

```sh
make tinyconfig
./scripts/config --file .config \
  -e BLK_DEV_INITRD \
  -e RD_LZMA \
  -e BINFMT_ELF \
  -e PRINTK \
  -e TTY \
  -e VT \
  -e VT_CONSOLE \
  -e FUTEX \
  -e POSIX_TIMERS \
  -e HIGH_RES_TIMERS \
  -e EPOLL \
  -e EVENTFD \
  -e SERIAL_8250 \
  -e SERIAL_8250_CONSOLE
make olddefconfig
```

or

```sh
make tinyconfig
./scripts/kconfig/merge_config.sh .config initramfs.fragment
make olddefconfig
```

If you want serial-only QEMU output with console=ttyS0, you may also want 8250 serial console support in the kernel, but that is separate from what fixed the Go panic.

```sh
nproc

cd linux 
make -j4
cp arch/x86/boot/bzImage ..
```

## initramfs

```sh
(cd fs && find . | cpio -o -H newc | lzma > ../init.cpio.lzma)
```

## QEMU

```sh
qemu-system-x86_64 -kernel bzImage -initrd init.cpio.lzma -append "rdinit=/init console=ttyS0,115200n8" -nographic -serial mon:stdio
```

## Image build (ISO or IMG)

```sh
sudo apt-get install \
fdisk \
util-linux \
e2fsprogs \
syslinux \
syslinux-common \
isolinux \
xorriso \
grub-pc-bin \
grub-common
```

```sh
qemu-system-x86_64 -cdrom os.iso -nographic -serial mon:stdio

qemu-system-x86_64 -drive file=usb.img,format=raw -nographic -serial mon:stdio
```
