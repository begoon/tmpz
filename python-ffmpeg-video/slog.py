import logging
import os
from typing import Any, cast

import flatten_json
import structlog
from structlog.typing import EventDict, WrappedLogger

GCP_MODE = os.getenv("K_SERVICE", False) or os.getenv("CLOUD_RUN_JOB", False)

configured = False


def get_logger() -> structlog.stdlib.BoundLogger:
    global configured

    if not configured:
        configure()

    configured = True

    return cast(structlog.stdlib.BoundLogger, structlog.get_logger())


def google_fields(
    logger: WrappedLogger,
    name: str,
    event_dict: EventDict,
) -> EventDict:
    if level := event_dict.get("level"):
        event_dict["severity"] = level
    if event_dict.get("event"):
        event_dict["message"] = event_dict.pop("event")
    return event_dict


def flattener(
    logger: WrappedLogger,
    name: str,
    event_dict: EventDict,
) -> EventDict:
    try:
        if event := event_dict.get("event"):
            assert isinstance(event, str)

            explicit_flatten = os.getenv("FLATTEN_LOG")
            if event.startswith("$") or explicit_flatten:
                if not explicit_flatten:
                    event = event[1:]

                flattened = flatten_json.flatten(
                    event_dict,
                    "|",
                    root_keys_to_ignore=["event", "timestamp", "level"],
                )

                def clean(v: Any) -> Any:
                    if not isinstance(v, str):
                        return v
                    return v.replace('"', "")

                msg = [f"{k}={clean(v)}" for k, (v) in flattened.items()]
                if len(msg) > 0:
                    event_dict["event"] = f"{event} {' '.join(msg)}"
    except Exception:
        pass
    return event_dict


def configure() -> None:
    console = structlog.dev.ConsoleRenderer(
        exception_formatter=structlog.dev.plain_traceback,
        pad_event_to=0,
        sort_keys=False,
        colors=not GCP_MODE,
        pad_level=False,
    )

    processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S:%f", utc=True),
    ]

    if GCP_MODE:
        processors.append(flattener)
        processors.append(google_fields)
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(console)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
