import logging
import os
import traceback
from typing import Final, cast

import structlog
from structlog.typing import EventDict, WrappedLogger

K_SERVICE = os.getenv("K_SERVICE", False)


def get_logger() -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger())


def severity_adder(
    logger: WrappedLogger,
    name: str,
    event_dict: EventDict,
) -> EventDict:
    if K_SERVICE and (level := event_dict.get("level")):
        event_dict["severity"] = level
    return event_dict


def configure(level: int = logging.NOTSET) -> None:
    console = structlog.dev.ConsoleRenderer(
        exception_formatter=structlog.dev.plain_traceback,
        pad_event=0,
        sort_keys=False,
        colors=not K_SERVICE,
        pad_level=False,
    )

    log_renderer = structlog.processors.JSONRenderer() if K_SERVICE else console

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=True),
            severity_adder,
            log_renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def format_exception(exception: Exception) -> str:
    trace_lines: Final = traceback.format_exception(exception)
    trace_string: Final = "".join(trace_lines)
    return trace_string


def summarize_exception(exception: BaseException) -> str:
    def summarize(e: BaseException) -> str:
        v = type(e).__name__
        if e.args:
            v += " " + ", ".join([f"[{x}]" for x in e.args])
        return v

    summary = summarize(exception)
    while cause := exception.__cause__:
        summary += " <~ " + summarize(cause)
        exception = cause
    return summary


logger: structlog.stdlib.BoundLogger = structlog.get_logger()
