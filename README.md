# TUM-Live-Voice-Service
Microservice that generates subtitles for TUM-Live.

## API

```bash
$ grpcurl -plaintext localhost:50051 list Subtitles
Subtitles.Generate
```

## Get it started 

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
$ docker build --no-cache . -t voice-service-image
[+] Building 0.4s (1/10)...
```

#### run application 

```bash
$ docker run -p 50051:50051 \
  --name voice-service \
  -v /srv/static:/data \
  -e CONFIG_FILE=/etc/config.yml \
  -e DEBUG=.\
  -d \
  voice-service-image
```
