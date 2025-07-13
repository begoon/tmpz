(async () => {
    const urlPattern = /iproov\.io/;
    if (!urlPattern.test(location.href)) return;

    const configurator = "/configurator";
    const i = location.href.indexOf(configurator);
    const url = i !== -1 ? location.href.substring(0, i + configurator.length) : location.origin;
    console.log("/health", url);

    const element = document.createElement("div");
    Object.assign(element.style, {
        position: "fixed",
        bottom: "10px",
        left: "10px",
        background: "rgba(0,0,0,0.7)",
        color: "#fff",
        padding: "5px 10px",
        fontSize: "16px",
        fontFamily: "monospace",
        borderRadius: "4px",
        zindex: 99999,
    });
    document.body.appendChild(element);

    let latencyTimer = undefined;
    async function latency() {
        if (latencyTimer) clearTimeout(latencyTimer);
        try {
            const started = performance.now();
            const response = await fetch(`${url}/health`, { credentials: "same-origin" });
            if (!response.ok) {
                console.warn("failed calling /health:", response.status, response.statusText);
                return;
            }
            const data = await response.json();
            const elapsed = performance.now() - started;
            element.textContent = `version ${data.version} | latency ${Math.round(elapsed)}ms`;
            if (false) latencyTimer = setTimeout(latency, 1000);
        } catch (e) {
            console.warn("failed calling /health:", e);
        }
    }
    await latency();
})();
