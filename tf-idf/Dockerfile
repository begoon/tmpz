FROM golang:1.23 as build

WORKDIR /

COPY go.* /

COPY data /data
COPY templates /templates

COPY index.gob /

COPY main.go /

COPY VERSION.txt /
COPY TAG.txt /

COPY .env /

RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /exe ./.

FROM gcr.io/distroless/static-debian12

COPY --from=build /exe /
ENTRYPOINT ["/exe"]