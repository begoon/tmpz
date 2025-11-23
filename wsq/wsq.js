let memory;

let malloc;
let free;

let wsq_decode;

let activeCanvas = null;

function render(bufferPtr, cols, rows, depth) {
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

    const bytesPerPixel = depth / 8; // 1 for 8-bit grayscale
    const numPixels = cols * rows;
    const bufSize = numPixels * bytesPerPixel;

    const src = new Uint8Array(memory.buffer, bufferPtr, bufSize);

    canvas.width = cols;
    canvas.height = rows;

    const imageData = ctx.createImageData(cols, rows);
    const data = imageData.data;

    if (depth === 8) {
        for (let i = 0; i < numPixels; i++) {
            const v = src[i];
            const j = i * 4;
            data[j] = v;
            data[j + 1] = v;
            data[j + 2] = v;
            data[j + 3] = 255;
        }
    } else {
        for (let i = 0; i < numPixels; i++) {
            const v = src[i * bytesPerPixel];
            const j = i * 4;
            data[j] = v;
            data[j + 1] = v;
            data[j + 2] = v;
            data[j + 3] = 255;
        }
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
    const { instance } = await WebAssembly.instantiateStreaming(fetch("wsq.wasm"), {
        env,
        wasi_snapshot_preview1,
    });
    console.log("WASM instance:", instance);
    memory = instance.exports.memory;
    malloc = instance.exports.malloc;
    free = instance.exports.free;
    wsq_decode = instance.exports.wsq_decode;
}

async function wsqToCanvas(url, canvas) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status} for ${url}`);

        const wsqArray = new Uint8Array(await response.arrayBuffer());
        const wsqSize = wsqArray.length;

        const ptr = malloc(wsqSize);
        const wsqBuffer = new Uint8Array(memory.buffer, ptr, wsqSize);
        wsqBuffer.set(wsqArray);

        activeCanvas = canvas;
        const ret = wsq_decode(ptr, wsqSize);
        activeCanvas = null;

        free(ptr);

        if (ret !== 0) {
            console.error("wsq_decode returned error", ret, "for", url);
        }
    } catch (e) {
        console.error("Error decoding WSQ", url, e);
    }
}

async function wsqRenderImages() {
    // find all <img> elements whose src ends with .wsq (case-insensitive)
    const images = Array.from(document.querySelectorAll("img")).filter((img) =>
        /\.wsq(\?|#|$)/i.test(img.getAttribute("src") || "")
    );

    if (images.length === 0) return;

    for (const image of images) {
        const src = image.getAttribute("src");

        const canvas = document.createElement("canvas");
        image.parentNode.insertBefore(canvas, image);
        image.remove();

        await wsqToCanvas(src, canvas);
    }
}

await initWasm();
await wsqRenderImages();
