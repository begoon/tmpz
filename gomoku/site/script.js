// script.js
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

const N = 15;
const BOARD = Array.from({ length: N }, () => Array.from({ length: N }, () => "."));

const HUMAN = 1; // X
const COMPUTER = 2; // O
const PLAYER_NAMES = { [HUMAN]: "X", [COMPUTER]: "O" };

let thinking = false;
let last_move = { r: -1, c: -1 };
let winner = null;

function update_thinking(on) {
    thinking = on;
    $("#thinking").style.display = on ? "block" : "none";
}

// worker RPC wiring
const worker = new Worker("wasm-worker.js", { type: "module" });

let requestID = 1;
const pending = new Map();

function callWorker(type, data = {}) {
    const id = requestID++;
    worker.postMessage({ id, type, ...data });
    return new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject });
        // (optional) add a timeout if needed
    });
}

worker.onmessage = (event) => {
    const msg = event.data;
    if (msg.type === "response") {
        const { id, ok, result, error } = msg;
        const job = pending.get(id);
        if (job) {
            pending.delete(id);
            ok ? job.resolve(result) : job.reject(error);
        }
        return;
    }

    // unsolicited notifications from worker
    switch (msg.type) {
        case "ready":
            console.log("WASM ready");
            break;
        case "console":
            // the worker consolidates lines, so just print them
            console.log(msg.text);
            break;
        case "status":
            $("#status").textContent = msg.text;
            break;
        default:
            // ignore
            break;
    }
};

function highlight_last_move(move) {
    const fields = $$(".field");
    for (const field of fields) {
        const row = Number(field.dataset.row);
        const col = Number(field.dataset.col);
        if (row === last_move.r && col === last_move.c) field.classList.remove("last-move");
        if (row === move.r && col === move.c) field.classList.add("last-move");
    }
    last_move = move;
}

async function have_winner() {
    const v = await callWorker("is_winner", { r: last_move.r, c: last_move.c });
    if (v !== 0) {
        alert(`Game over! Winner: ${PLAYER_NAMES[v]}`);
        winner = v;
        return v;
    }
    return 0;
}

async function main() {
    const board = $("#board");

    for (let r = 0; r < 15; r++) {
        const field = document.createElement("div");
        field.classList.add("legend");
        field.textContent = String.fromCharCode(65 + r);
        board.appendChild(field);
    }
    const spacer = document.createElement("div");
    board.appendChild(spacer);

    for (let r = 0; r < 15; r++) {
        for (let c = 0; c < 15; c++) {
            const field = document.createElement("div");
            field.classList.add("field");
            field.dataset.row = r;
            field.dataset.col = c;
            if (BOARD[r][c] !== ".") field.textContent = BOARD[r][c];
            board.appendChild(field);
        }
        const legend = document.createElement("div");
        legend.classList.add("legend");
        legend.textContent = (r + 1).toString();
        board.appendChild(legend);
    }

    // start worker & WASM runtime
    await callWorker("start"); // loads wasm, allocates & init()

    // optional: ask the worker to print the initial board to console
    await callWorker("print_board");

    board.addEventListener("click", async (event) => {
        if (thinking || winner) return;

        const target = event.target;
        if (!target.classList.contains("field")) return;

        const row = Number(target.dataset.row);
        const col = Number(target.dataset.col);
        if (BOARD[row][col] !== ".") return;

        // Human move
        BOARD[row][col] = PLAYER_NAMES[HUMAN];
        target.textContent = PLAYER_NAMES[HUMAN];

        await callWorker("place", { r: row, c: col, player: HUMAN });
        await callWorker("print_board_at", { r: row, c: col });

        highlight_last_move({ r: row, c: col });

        if (await have_winner()) return;

        // computer thinking
        update_thinking(true);

        // let UI show spinner right away (no heavy work on main now, but this helps)
        await new Promise((r) => setTimeout(r, 0));

        // ask worker to compute best move (heavy)
        const start = performance.now();
        const move = await callWorker("choose_move", { depth: 5, player: COMPUTER });
        const end = performance.now();

        const r = (move >> 8) & 0xff;
        const c = move & 0xff;
        const msg = `computer move (${String.fromCharCode(65 + c)}${r + 1}) in ${(end - start).toFixed(2)} ms`;
        console.log(msg);

        update_thinking(false);
        $("#status").textContent += `| ${msg}`;

        await callWorker("place", { r, c, player: COMPUTER });
        await callWorker("print_board_at", { r, c });

        BOARD[r][c] = PLAYER_NAMES[COMPUTER];
        for (const field of $$(".field")) {
            if (Number(field.dataset.row) === r && Number(field.dataset.col) === c) {
                field.textContent = PLAYER_NAMES[COMPUTER];
                break;
            }
        }

        highlight_last_move({ r, c });
        await have_winner();
    });
}

window.onload = main;
