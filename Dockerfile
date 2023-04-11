FROM python:3.9-slim as builder

ADD requirements.txt .

# Dependencies
RUN apt-get update && apt-get install -y git &&\
         pip install --user --no-cache-dir -r requirements.txt 

FROM python:3.9-slim

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y ffmpeg

ADD voice/ ./voice/
ADD config.yml .

COPY --from=builder /root/.local /root/.local

CMD ["python", "./voice/voice.py"]
