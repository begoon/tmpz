import slog

slog.configure()

logger = slog.get_logger()

logger.info("ha?")

try:
    try:
        1 / 0
    except Exception as e:
        raise ValueError("oops") from e
except Exception as e:
    logger.error(
        "error",
        summary=slog.summarize_exception(e),
        exception=slog.format_exception(e),
    )
