FROM python:3.12-slim

RUN pip install --upgrade pip
RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY main.py ./

RUN poetry install

CMD poetry run python main.py
