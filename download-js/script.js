const defaultProgressBar = {
    init: () => {
        const bar = document.createElement("div");
        Object.assign(bar.style, {
            visibility: "visible",
            position: "fixed",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "500px",
            height: "20px",
            backgroundColor: "#ddd",
            borderRadius: "5px",
            boxShadow: "0 0 10px rgba(0, 0, 0, 0.5)",
            padding: "1em 2em 2em 2em",
            fontFamily: "consolas, monospace",
        });
        const filler = document.createElement("div");
        Object.assign(filler.style, {
            width: "100%",
            height: "100%",
            backgroundColor: "#777",
        });
        bar.appendChild(filler);
        const text = document.createElement("div");
        Object.assign(text.style, {
            width: "0%",
            height: "100%",
            backgroundColor: "#fff",
            width: "100%",
            textAlign: "center",
        });
        bar.appendChild(text);
        bar.lastElementChild.textContent = "archiving...";
        document.body.appendChild(bar);
        return bar;
    },
    start: (bar) => {
        bar.lastElementChild.textContent = "";
    },
    progress: (bar, { length, position }) => {
        const percetange = (position / length) * 100;
        bar.firstElementChild.style.width = percetange + "%";
        bar.lastElementChild.textContent =
            `downloading... ` +
            `${percetange.toFixed(2)}% ` +
            `| ${position}/${length} `;
    },
    finish: (bar) => {
        bar.style.visibility = "hidden";
        document.body.removeChild(bar);
    },
};

async function download(url, progressbar = defaultProgressBar) {
    const bar = progressbar.init();

    console.log("downloading " + url);
    let response = await fetch(url, { mode: "cors" });
    console.log("response: " + response.status);

    progressbar.start(bar);

    const contentLength = +response.headers.get("Content-Length");
    console.log("size", contentLength);
    const name = response.headers
        .get("Content-Disposition")
        .split("=")[1]
        .slice(1, -1);
    console.log("name", name);

    const bytes = await readStream(response.body, (n) =>
        progressbar.progress(bar, { length: contentLength, position: n })
    );
    console.log(`${name}: received ${bytes.length} bytes`);

    progressbar.finish(bar);

    const tarred = await uncompress(bytes);
    const files = untar(tarred);

    for (let { name, size, file } of files) {
        let element;
        if (name.includes(".json")) {
            element = document.createElement("pre");
            element.textContent = new TextDecoder().decode(file);
        } else {
            element = document.createElement("img");
            const blob = new Blob([file], { type: "image/png" });
            element.src = URL.createObjectURL(blob);
            element.style.maxWidth = "600px";
        }
        const p = document.createElement("p");
        p.textContent = `${name} (${size} bytes)`;
        document.body.appendChild(p);
        document.body.appendChild(element);
    }

    return { name, bytes };
}

function asString(bytes) {
    return new TextDecoder().decode(bytes).replace(/\0.*$/, "");
}

function untar(bytes) {
    let i = 0;
    const files = [];
    while (i < bytes.length) {
        const name = asString(bytes.slice(i, i + 100));
        const size = parseInt(asString(bytes.slice(i + 124, i + 136)), 8);
        const file = bytes.slice(i + 512, i + 512 + size);
        if (name) {
            files.push({ name, size, file });
            console.log(i, name, size);
        }
        const last = size & 0x1ff;
        i += 512 + size + (last ? 512 - last : 0);
    }
    return files;
}

async function uncompress(bytes) {
    const format = "gzip";
    console.log(`uncompressing/${format}`, bytes.length, "bytes");
    const stream = createStream(bytes).pipeThrough(
        new DecompressionStream(format)
    );
    const uncompressed = await readStream(stream);
    console.log("uncompressed", uncompressed.length, "bytes");
    return uncompressed;
}

async function clicker(file) {
    let link = document.createElement("a");
    link.download = file.name;
    link.href = URL.createObjectURL(new Blob([file.bytes]));
    link.click();
    URL.revokeObjectURL(link.href);
}

const createStream = (array) => {
    return new ReadableStream({
        start: (controller) => {
            controller.enqueue(array);
            controller.close();
        },
    });
};

const readStream = async (stream, progress = null) => {
    const chunks = [];
    let length = 0;
    for await (let chunk of streamIterator(stream)) {
        chunks.push(chunk);
        length += chunk.length;
        if (progress) progress(length);
    }
    const bytes = new Uint8Array(length);
    let i = 0;
    for (let chunk of chunks) {
        bytes.set(chunk, i);
        i += chunk.length;
    }
    return bytes;
};

async function* streamIterator(stream) {
    const reader = stream.getReader();
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) return;
            yield value;
        }
    } finally {
        reader.releaseLock();
    }
}
