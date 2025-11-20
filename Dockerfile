FROM golang:1.25.1-alpine AS builder

WORKDIR /app

# Copy go.mod and go.sum to leverage Docker's layer caching
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o /voice-service cmd/voice-service/main.go

FROM alpine:latest

COPY --from=builder /voice-service /voice-service

RUN apk add ffmpeg

EXPOSE 50053

COPY config.json /root/.docker/config.json

ENTRYPOINT ["/voice-service"]