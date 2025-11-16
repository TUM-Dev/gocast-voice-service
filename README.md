# Gocast Voice Service

Microservice that generates subtitles for [TUM-Live](https://live.rbg.tum.de). Using [whisperX](https://github.com/m-bain/whisperX)

## Workflow

```
                     ┌──────────┐
      ┌──────────────┤  WORKER  │
      │              └──────────┘
      │
      │
      │ 1) .NotifyUploadFinished
      │
      │
      │
      │
┌─────▼──────┐       2) .Generate         ┌───────────┐
│            ├────────────────────────────►           │
│            │                            │   VOICE   │
│  TUM-LIVE  │                            │  SERVICE  │
│            │                            │           │
├────────────◄────────────────────────────┼───────────┤
│  RECEIVER  │        3) .Receive         │ GENERATOR │
└────────────┘                            └───────────┘
```

## API

```bash
$ grpcurl -plaintext localhost:50055 list live.voice.v1.SubtitleGenerator

live.voice.v1.SubtitleGenerator.Generate
```

```bash
$ grpcurl -plaintext \
  -d '{"stream_id":1, "source_file":"/tmp/120.mp4"}' \
  -import-path ./protobufs -proto subtitles.proto \
  localhost:50055 live.voice.v1.SubtitleGenerator.Generate
```

## Configuration

The service can be configured using the following command-line flags:

| Flag          | Description                                | Default         |
|---------------|--------------------------------------------|-----------------|
| `-parallelism`| Number of concurrent jobs                    | `3`             |
| `-hw-accel`   | Enable hardware acceleration               | `true`          |
| `-queue-size` | Size of the job queue                      | `10`            |
| `-target`     | gocast server to push subtitles to         | `localhost:50053`|

## Running with Docker

The `voice-service` interacts with the Docker daemon to manage its operations. Therefore, when running the service in a Docker container, you need to mount the Docker socket.

1.  **Build the Docker image:**

    ```bash
    docker build -t gocast-voice-service .
    ```

2.  **Run the Docker container:**

    You need to mount the Docker socket (`/var/run/docker.sock`) and map the gRPC port (`50053`).

    ```bash
    docker run -d \
      -p 50053:50053 \
      -v /var/run/docker.sock:/var/run/docker.sock \
      gocast-voice-service [flags]
    ```

    Replace `[flags]` with any desired command-line flags for the `voice-service` (e.g., `-parallelism 4 -target some-host:50053`).

    **Example:**

    ```bash
    docker run -d \
      -p 50053:50053 \
      -v /var/run/docker.sock:/var/run/docker.sock \
      gocast-voice-service -parallelism 4 -target my-gocast-server:50053
    ```

### Batch tool

`cmd/batch` contains a tool that triggers subtitle generation for 
an entire gocast course:

```bash
go run cmd/batch/main.go --admintoken=secret '--dsn=user:password@tcp(localhost:3006)/db' --srv=localhost:50051 --lang=en --course=123
```

The admintoken can be configured in the gocast edge server config.
