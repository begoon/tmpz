FROM golang:latest AS builder
WORKDIR /build
COPY go.mod init.go ./
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o init init.go

FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    linux-image-generic \
    cpio \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY --from=builder /build/init ./init

# Extract bzImage from installed kernel
RUN cp /boot/vmlinuz-* ./bzImage

# Create initramfs cpio archive
RUN mkdir initramfs && \
    cp init initramfs/init && \
    chmod +x initramfs/init && \
    cd initramfs && \
    find . | cpio -o -H newc > /build/init.cpio
