# TUM-Live-Voice-Service

Microservice that generates subtitles for [TUM-Live](https://live.rbg.tum.de).

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

voice.SubtitleGenerator.Generate
```

```bash
$ grpcurl -plaintext \
  -d '{"stream_id":1, "source_file":"/tmp/120.mp4"}' \
  -import-path ./protobufs -proto subtitles.proto \
  localhost:50055 live.voice.v1.SubtitleGenerator.Generate
```

## Installation

### Python virtual environment

```bash 
$ git clone https://github.com/TUM-Dev/TUM-Live-Voice-Service.git
Cloning into 'TUM-Live-Voice-Service'...
$ cd TUM-Live-Voice-Service
$ python -m venv venv
$ source venv/bin/activate
(venv) $ pip install --no-cache-dir -r requirements.txt 
(venv) $ DEBUG=. CONFIG_FILE=./config.yml python3.9 subtitles/subtitles.py
...
```

Or simply use an open source IDE like [PyCharm CE](https://www.jetbrains.com/pycharm/).

### Docker

```bash
$ docker run -p 50055:50055 \
  --name voice-service \
  -v /srv/static:/data \
  -e CONFIG_FILE=./config.yml \
  -e DEBUG=.\
  -d \
  ghcr.io/tum-dev/tum-live-voice-service:latest
```

## Configuration 

You can configure the application with: 
- YAML file 
- .env file and environment variables

**Configuration precedence** (`>` = _overwrites_): `environment > .env > .yml`

<details><summary>Examplary .env file </summary>
<p>

```bash
API_PORT=51000
REC_HOST=127.0.0.1
REC_PORT=51001
VOSK_MODEL_DIR=/data
VOSK_DWNLD_URLS=https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip,https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip
VOSK_MODELS=model-fr:fr,model-en:en
WHISPER_MODEL=medium
MAX_WORKERS=10
```
</p>
</details>

<details><summary>Examplary YAML file </summary>
<p>

```YAML
api:
  port: 50055
receiver:
  host: localhost
  port: 50053
transcriber: 'whisper'
vosk:
  model_dir: '/data'
  download_urls:
    - https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    - https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip
  models:
    - name: 'vosk-model-small-en-us-0.15'
      lang: 'en'
    - name: 'data/vosk-model-small-de-0.15'
      lang: 'de'
whisper:
  model: 'tiny'
max_workers: 10
```
</p>
</details>

## Transcribers

Currently following transcribers are implemented and can be specified in the configuration: 
  * [whisper](https://github.com/openai/whisper)
  * [vosk](https://github.com/alphacep/vosk-api)
  
Which transcriber one chooses depends immensely on the use case and computing power available. We found that whisper produces much higher quality results, especially regarding punctuation, but is much more compute-heavy.

## License

[MIT](https://choosealicense.com/licenses/mit/)
