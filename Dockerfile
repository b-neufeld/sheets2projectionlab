# FROM python:3.6.12-alpine3.12
FROM python:3

COPY . .

RUN pip install -r requirements.txt

RUN crontab crontab

CMD ["crond", "-f"]

LABEL org.opencontainers.image.source="https://github.com/b-neufeld/sheets2projectionlab"