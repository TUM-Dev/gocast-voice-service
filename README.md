# TUM-Live-Voice-Service

Microservice that generates subtitles for [TUM-Live](https://live.rbg.tum.de).

## Usage

### Workflow

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

### API

```bash
$ grpcurl -plaintext localhost:50055 list voice.SubtitleGenerator

voice.SubtitleGenerator.Generate
```

```bash
$ grpcurl -plaintext \
  -d '{"stream_id":1, "source_file":"/tmp/120.mp4"}' \
  -import-path ./protobufs -proto subtitles.proto \
  localhost:50055 voice.SubtitleGenerator.Generate
```

## Installation

### Run with virtual environment

```bash 
$ git clone https://github.com/TUM-Dev/TUM-Live-Voice-Service.git
Cloning into 'TUM-Live-Voice-Service'...
...
$ cd TUM-Live-Voice-Service
$ python -m venv venv
$ source venv/bin/activate
(venv) $ pip install --no-cache-dir -r requirements.txt 
(venv) $ DEBUG=. CONFIG_FILE=./config.yml python3.9 subtitles/subtitles.py
DEBUG:asyncio:Using selector: KqueueSelector
DEBUG:grpc._cython.cygrpc:Using AsyncIOEngine.POLLER as I/O engine
DEBUG:root:loading SubtitleService with models: ['/data/vosk-model-small-en-us-0.15/', '/data/vosk-model-small-de-0.15/']
DEBUG:root:starting server with reflection activated.
INFO:root:listening at :50051
...
```

Or simply use an open source IDE like [PyCharm CE](https://www.jetbrains.com/pycharm/).

### Docker

#### build

```bash
$ docker build --no-cache -t voice-service-image .
[+] Building 0.4s (1/10)...
```

#### run application

```bash
$ docker run -p 50055:50055 \
  --name voice-service \
  -v /srv/static:/data \
  -e CONFIG_FILE=./config.yml \
  -e DEBUG=.\
  -d \
  voice-service-image
```

### Configuration 

You can configure the application with: 
- YAML file 
- .env file and environment variables

**Configuration precedence** 

`>` = _overwrites_: `environment > .env > .yml`

#### Examplary .env file 

```bash
API_PORT=51000
REC_HOST=127.0.0.1
REC_PORT=51001
VOSK_MODELS=/data/fr:fr,/data/en:en
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
