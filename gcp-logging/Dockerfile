ARG GO_VERSION=1.20

FROM golang:${GO_VERSION}-alpine AS build

WORKDIR /src

COPY main.go .
COPY go.* .

RUN GOOS=linux GOARCH=amd64 go build -o /job ./main.go

FROM gcr.io/distroless/static AS final

COPY --from=build /job /job

CMD ["/job"]
