let instance;
let memory;

let handle = 0;

let consoleBuffer = "";

function readStr(ptr, len) {
    const bytes = new Uint8Array(memory.buffer, ptr, len);
    return new TextDecoder("utf-8").decode(bytes);
}

function respond(id, ok, result, error) {
    postMessage({ type: "response", id, ok, result, error });
}

const env = {
    console: (ptr, len) => {
        const text = readStr(ptr, len);
        consoleBuffer += text;
        if (text.endsWith("\n") || text.endsWith("\r")) {
            postMessage({ type: "console", text: consoleBuffer.trim() });
            consoleBuffer = "";
        }
    },
    status: (ptr, len) => {
        const text = readStr(ptr, len);
        // Forward to main thread; it will update DOM and allow paint
        postMessage({ type: "status", text });
    },
};

// Command handlers (RPC)
const handlers = {
    // loads wasm, allocates a game handle and initializes it
    async start({ id }) {
        if (!instance) {
            const resp = await fetch("wasm.wasm");
            const { instance: inst } = await WebAssembly.instantiateStreaming(resp, { env });
            instance = inst;
            memory = instance.exports.memory;
        }
        if (!handle) {
            handle = instance.exports.alloc();
            instance.exports.init(handle);
        }
        postMessage({ type: "ready" });
        respond(id, true, true);
    },

    // debug helpers (optional)
    print_board({ id }) {
        instance.exports.print_board(handle);
        respond(id, true, true);
    },

    print_board_at({ id, r, c }) {
        instance.exports.print_board_at(handle, r, c);
        respond(id, true, true);
    },

    // game operations
    place({ id, r, c, player }) {
        instance.exports.place(handle, r, c, player);
        respond(id, true, true);
    },

    is_winner({ id, r, c }) {
        const v = instance.exports.is_winner(handle, r, c);
        respond(id, true, v);
    },

    choose_move({ id, depth, player }) {
        // heavy computation happens here off the main thread
        const move = instance.exports.choose_move(handle, depth, player);
        respond(id, true, move);
    },

    free({ id }) {
        if (instance && handle) {
            instance.exports.free(handle);
            handle = 0;
        }
        respond(id, true, true);
    },
};

// generic onmessage to route requests
onmessage = async (event) => {
    const { id, type, ...rest } = event.data || {};
    const func = handlers[type];
    if (!func) {
        respond(id, false, null, `unknown worker command: ${type}`);
        return;
    }
    try {
        await func({ id, ...rest });
    } catch (err) {
        respond(id, false, null, String(err && err.message ? err.message : err));
    }
};
