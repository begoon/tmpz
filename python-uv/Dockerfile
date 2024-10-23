FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

ADD pyproject.toml .
ADD uv.lock .

ADD main.py .

RUN uv sync --frozen

CMD uv run uvicorn main:application --port 8000 --host 0.0.0.0
