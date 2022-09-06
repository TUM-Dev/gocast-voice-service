FROM python:3.9-slim

WORKDIR /usr/src/app

ADD subtitles/ ./subtitles/
ADD requirements.txt .

# Vosk Dependencies
RUN apt-get update -y && apt-get install -y ffmpeg


# Install Python modules
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./subtitles/subtitles.py"]
