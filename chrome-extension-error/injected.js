(function () {
    let reported = false;

    const endpoint = () => {
        if (!reported) {
            console.info("CONSOLE =", window.CONSOLE || "off");
            reported = true;
        }
        return window.CONSOLE;
    };
    console.log("chrome console initialized");

    function deliver(payload) {
        const url = endpoint();
        if (!url) return;
        fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        }).catch(() => {});
    }

    window.onerror = function (message, source, lineno, colno, error) {
        deliver({
            type: "window.onerror",
            message,
            source,
            lineno,
            colno,
            stack: error?.stack || null,
            timestamp: new Date().toISOString(),
        });
    };

    window.addEventListener("unhandledrejection", function (event) {
        deliver({
            type: "unhandledrejection",
            reason: event.reason?.message || String(event.reason),
            stack: event.reason?.stack || null,
            timestamp: new Date().toISOString(),
        });
    });

    const wrapConsole = (method) => {
        const original = console[method];
        console[method] = function (...args) {
            deliver({
                type: `console.${method}`,
                args,
                timestamp: new Date().toISOString(),
            });
            original.apply(console, args);
        };
    };

    ["log", "warn", "error"].forEach(wrapConsole);
})();
