FROM python:3.9-slim

WORKDIR /usr/src/app

ADD subtitles/ ./subtitles/
ADD requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./subtitles/subtitles.py"]
