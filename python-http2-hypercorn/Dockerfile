FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /runtime

COPY pyproject.toml uv.lock ./
RUN uv sync

COPY main.py client.py ./

CMD ["uv", "run", "hypercorn", "--bind", "0.0.0.0:8000", "main:application"]
