FROM alpine:latest

RUN apk add --no-cache musl-dev libcurl curl-dev libcurl4-openssl-dev
RUN apk add zig

COPY main.c /

RUN zig cc -lcurl -target x86_64-linux-gnu -o main main.c
RUN ls -al http_client
RUN ldd http_client

CMD ["./main", "https://api.ipify.org"]
