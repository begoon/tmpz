async function download(url) {
    const progressbar = {
        init: () => {
            const bar = document.createElement("div");
            Object.assign(bar.style, {
                visibility: "visible",
                position: "fixed",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                width: "300px",
                height: "20px",
                backgroundColor: "#ddd",
            });
            const filler = document.createElement("div");
            Object.assign(filler.style, {
                width: "0%",
                height: "100%",
                backgroundColor: "#333",
            });
            bar.appendChild(filler);
            bar.firstElementChild.textContent = "archiving...";
            document.body.appendChild(bar);
            return bar;
        },
        start: (bar) => {
            bar.firstElementChild.textContent = "";
        },
        progress: (bar, { length, position, color }) => {
            bar.firstElementChild.style.width = `${(position / length) * 100}%`;
        },
        finish: (bar) => {
            bar.style.visibility = "hidden";
            document.body.removeChild(bar);
        },
    };

    const bar = progressbar.init();

    console.log("downloading " + url);
    let response = await fetch(url, { mode: "cors" });
    console.log("response: " + response.status);

    progressbar.start(bar);

    const reader = response.body.getReader();
    const sz = +response.headers.get("Content-Length");
    console.log("size", sz);
    const name = response.headers
        .get("Content-Disposition")
        .split("=")[1]
        .slice(1, -1);
    console.log("name", name);

    let n = 0;
    let chunks = [];
    while (true) {
        const { done, value } = await reader.read();
        if (done) {
            break;
        }
        chunks.push(value);
        n += value.length;
        console.log(`received ${n} of ${sz}`);

        progressbar.progress(bar, { length: sz, position: n });
    }

    let bytes = new Uint8Array(n);
    let position = 0;
    for (let chunk of chunks) {
        bytes.set(chunk, position);
        position += chunk.length;
    }
    console.log(`received ${bytes.length} bytes`);

    progressbar.finish(bar);

    let link = document.createElement("a");
    link.download = name;
    link.href = URL.createObjectURL(new Blob([bytes]));
    link.click();
    URL.revokeObjectURL(link.href);
}
