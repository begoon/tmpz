let memory;

let malloc;
let free;

let qoi_render;

let activeCanvas = null;

function render(bufferPtr, cols, rows, channels) {
    console.log("render called with", { bufferPtr, cols, rows, channels });
    if (!memory) {
        console.error("render called before memory is ready");
        return;
    }

    const canvas = activeCanvas;
    if (!canvas) {
        console.error("render called but no activeCanvas set");
        return;
    }

    const ctx = canvas.getContext("2d");

    const numPixels = cols * rows;
    const bufSize = numPixels * channels;

    const raw = new Uint8Array(memory.buffer, bufferPtr, bufSize);

    canvas.width = cols;
    canvas.height = rows;

    const imageData = ctx.createImageData(cols, rows);
    const data = imageData.data;

    for (let offset = 0; offset < numPixels; offset++) {
        const i = offset * channels;
        const j = offset * 4;

        data[j] = raw[i]; // R
        data[j + 1] = raw[i + 1]; // G
        data[j + 2] = raw[i + 2]; // B
        data[j + 3] = channels === 4 ? raw[i + 3] : 255; // A
    }
    ctx.putImageData(imageData, 0, 0);
}

// stub for any WASI import
const wasi_snapshot_preview1 = new Proxy(
    {},
    {
        get(target, prop) {
            if (!(prop in target)) {
                target[prop] = (...args) => 0;
            }
            return target[prop];
        },
    }
);

// stub for any unknown env.* import, but keep real render/abort
const env = new Proxy(
    {
        render,
        abort: () => {
            throw new Error("WASM abort");
        },
    },
    {
        get(target, prop) {
            if (prop in target) return target[prop];
            const fn = (...args) => 0;
            target[prop] = fn;
            return fn;
        },
    }
);

async function initWasm() {
    const { instance } = await WebAssembly.instantiateStreaming(fetch("qoi.wasm"), {
        env,
        wasi_snapshot_preview1,
    });
    console.log("WASM instance:", instance);
    memory = instance.exports.memory;
    malloc = instance.exports.malloc;
    free = instance.exports.free;
    qoi_render = instance.exports.qoi_render;
}

async function qoiToCanvas(url, canvas) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status} for ${url}`);

        const qoiArray = new Uint8Array(await response.arrayBuffer());
        const qoiSize = qoiArray.length;

        const ptr = malloc(qoiSize);
        const qoiBuffer = new Uint8Array(memory.buffer, ptr, qoiSize);
        qoiBuffer.set(qoiArray);

        activeCanvas = canvas;
        const ret = qoi_render(ptr, qoiSize);
        activeCanvas = null;

        free(ptr);

        if (ret !== 0) {
            console.error("qoi_render returned error", ret, "for", url);
        }
    } catch (e) {
        console.error("Error decoding QOI", url, e);
    }
}

async function qoiRenderImages() {
    // find all <img> elements whose src ends with .qoi (case-insensitive)
    const images = Array.from(document.querySelectorAll("img")).filter((img) =>
        /\.qoi(\?|#|$)/i.test(img.getAttribute("src") || "")
    );

    if (images.length === 0) return;

    for (const image of images) {
        const src = image.getAttribute("src");

        const canvas = document.createElement("canvas");
        image.parentNode.insertBefore(canvas, image);
        image.remove();

        await qoiToCanvas(src, canvas);
    }
}

await initWasm();
await qoiRenderImages();
