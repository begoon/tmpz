# AGENTS.md

## Project Overview

This is a FastAPI web application deployed on FastAPI Cloud. It provides a simple REST API.

## Tech Stack

- **Language:** Python 3.13
- **Framework:** FastAPI (with standard extras including uvicorn, etc.)
- **Package Manager:** uv
- **Deployment:** FastAPI Cloud

## Project Structure

- `main.py` — Application entrypoint. Defines the FastAPI `app` instance and route handlers.
- `pyproject.toml` — Project metadata and dependencies.
- `.fastapicloud/` — FastAPI Cloud deployment config (not committed to git).
- `.python-version` — Pins Python 3.13.

## Development

### Setup

```bash
uv sync
```

### Run locally

```bash
uv run fastapi dev main.py
```

The dev server runs at `http://localhost:8000` with auto-reload.

### Add dependencies

```bash
uv add <package>
```

## Conventions

- The FastAPI app instance is defined in `main.py` as `app`.
- Route handlers should be async (`async def`).
- Keep the `.fastapicloud/` directory out of version control.

## Testing

Tests use `pytest` with `httpx.AsyncClient` via `pytest-anyio` for async endpoint testing.

- Test files live alongside source files, named `*_test.py` (e.g., `main_test.py`).

```bash
uv run pytest              # run all tests
uv run pytest main_test.py -v  # run specific file, verbose
```
