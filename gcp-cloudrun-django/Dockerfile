FROM python:3.11.1-slim

RUN pip install poetry

WORKDIR /

COPY poetry.lock pyproject.toml /
RUN poetry install

COPY ./application /application
COPY ./master /master
COPY ./templates /templates
COPY ./static /static
COPY ./staticfiles /staticfiles

ENV FORWARDED_ALLOW_IPS="*"
ENV PORT=8000
ENV HOME=/root

CMD \
    poetry run uvicorn application.asgi:application \
    --host 0.0.0.0 \
    --port $PORT \
    --forwarded-allow-ips "$FORWARDED_ALLOW_IPS"
