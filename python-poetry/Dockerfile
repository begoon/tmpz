FROM python:3.12-slim as build

RUN pip install poetry

WORKDIR /app

COPY poetry.* pyproject.toml ./
RUN poetry --no-cache install

COPY app .

# ---

FROM python:3.12-alpine

WORKDIR /app

COPY --from=build /app .

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "main.py"]
