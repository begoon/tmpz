FROM golang:1.24 AS builder

WORKDIR /

COPY . .
RUN CGO_ENABLED=0 go build -o /exe -trimpath -ldflags '-w -s' ./main.go

FROM scratch
COPY --from=builder /exe /exe
ENTRYPOINT [ "/exe" ]
