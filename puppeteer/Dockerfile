ARG GO_VERSION=1.24

FROM golang:${GO_VERSION}-alpine AS build

WORKDIR /

COPY go.mod go.sum main.go ./
COPY content content

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /exe main.go

FROM chromedp/headless-shell:latest

COPY --from=build /exe /

ENTRYPOINT ["/exe"]
