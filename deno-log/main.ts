import * as log from "https://deno.land/std@0.212.0/log/mod.ts";

// Simple default logger out of the box. You can customize it
// by overriding logger and handler named "default", or providing
// additional logger configurations. You can log any data type.
log.setup({
    handlers: {
        jsonStdout: new log.handlers.ConsoleHandler("DEBUG", {
            formatter: log.formatters.jsonFormatter,
            useColors: true,
        }),
    },

    loggers: {
        default: {
            level: "DEBUG",
            handlers: ["jsonStdout"],
        },
    },
});

log.debug("Hello world");
log.info(123456);
log.warn(true);
log.error("bang", { foo: "bar", fizz: "bazz" });
log.critical("500 Internal server error");
