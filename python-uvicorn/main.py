import contextvars
import logging
import os
import traceback
from dataclasses import dataclass
from traceback import format_exception

from fastapi import FastAPI
from fastapi.responses import JSONResponse

application = FastAPI()


@application.exception_handler(Exception)
async def unhandled(request, exc):
    error = str(exc)
    stack_trace = "".join(format_exception(exc)).splitlines()
    return JSONResponse(
        content={"error": error, "stack_trace": stack_trace},
        status_code=418,
    )


@dataclass
class Context:
    original_traceback: bool = False


context = contextvars.ContextVar[Context]("context", default=None)
context.set(Context())


@application.get("/")
async def main():
    return {"message": "OK"}


@application.get("/boom")
async def boom():
    raise Exception("boom!")


def application_traceback(traceback: list[str]) -> list[str]:
    def skip(v: str) -> bool:
        v = v.strip()
        if v.startswith("|") or v.startswith("+"):
            return True
        if "lib/python" in v or ".venv" in v or "in tracer" in v:
            return True
        if "call_next" in v:
            return True
        return False

    filtered = [v for v in traceback if not skip(v)]
    cwd = os.getcwd() + "/"
    return [line.replace(cwd, "") for line in filtered]


class ApplicationTracebackFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info:
            trace = traceback.format_exception(*record.exc_info)
            record.exc_text = "".join(application_traceback(trace))

        return True


logging.getLogger("uvicorn.error").addFilter(ApplicationTracebackFilter())
logging.getLogger("hypercorn.error").addFilter(ApplicationTracebackFilter())
