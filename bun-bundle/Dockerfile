FROM oven/bun:latest AS build
WORKDIR /app
COPY index.ts ./
COPY static ./static/
RUN bun build --compile --minify --target=bun-linux-x64-musl ./index.ts $(find static -type f) --outfile exe

FROM alpine:latest AS libs
RUN apk add --no-cache libstdc++ libgcc

FROM scratch
COPY --from=libs /lib/ld-musl-* /lib/
COPY --from=libs /usr/lib/libstdc++.so.6 /usr/lib/
COPY --from=libs /usr/lib/libgcc_s.so.1 /usr/lib/
COPY --from=build /app/exe /exe
EXPOSE 3000
ENTRYPOINT ["/exe"]
