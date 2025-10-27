const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

const N = 15;

const BOARD = Array.from({ length: N }, () => Array.from({ length: N }, () => "."));

function boardString(move) {
    try {
        if (move) BOARD[move.r][move.c] = "X";
        return BOARD.map((r) => r.join(""));
    } finally {
        if (move) BOARD[move.r][move.c] = ".";
    }
}

async function main() {
    const go = new Go(); // defined by wasm_exec.js
    const { instance } = await WebAssembly.instantiateStreaming(fetch("gomoku.wasm"), go.importObject);
    console.log("WASM loaded");
    go.run(instance);

    const board = $("#board");

    let thinking = false;
    let lastMove = { r: -1, c: -1 };
    let winner = null;

    function updateThinking(on) {
        thinking = on;
        $("#thinking").style.display = on ? "block" : "none";
    }

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
            if (BOARD[r][c] !== ".") {
                field.textContent = BOARD[r][c];
            }
            board.appendChild(field);
        }
        const legend = document.createElement("div");
        legend.classList.add("legend");
        legend.textContent = (r + 1).toString();
        board.appendChild(legend);
    }

    await evaluation();

    async function isWinner() {
        const result = window.endgame(boardString());
        console.log("endgame:", result);
        if (result.winner !== ".") {
            alert(`Game over! Winner: ${result.winner}`);
            winner = result.winner;
            return result.winner;
        }
    }

    async function evaluation() {
        const result = window.evaluate(boardString());
        console.log("evaluation:", result);
        console.log(JSON.stringify(result));
        $("#evaluation").textContent = `evaluation: ${result.value}`;
    }

    function highlightLastMove(move) {
        const fields = $$(".field");
        for (const field of fields) {
            const row = Number(field.dataset.row);
            const col = Number(field.dataset.col);
            if (row === lastMove.r && col === lastMove.c) {
                field.classList.remove("last-move");
            }
            if (row === move.r && col === move.c) {
                field.classList.add("last-move");
            }
        }
        lastMove = move;
    }

    board.addEventListener("click", async (event) => {
        if (thinking || winner) return;

        const target = event.target;
        if (target.classList.contains("field")) {
            const row = target.dataset.row;
            const col = target.dataset.col;
            if (BOARD[row][col] === ".") {
                console.log(`field clicked: (${row}, ${col})`);
                BOARD[row][col] = "X";
                target.textContent = "X";

                highlightLastMove({ r: Number(row), c: Number(col) });

                if (await isWinner()) {
                    return;
                }

                await evaluation();

                updateThinking(true);
                await new Promise((r) => setTimeout(r, 100)); // allow UI to update

                const response = window.minimax(boardString(), 2);

                updateThinking(false);

                console.log("minimax:", response);
                const { r, c } = response.move;
                const { duration } = response;
                $("#duration").textContent = `${duration}s`;

                BOARD[r][c] = "O";
                const fields = $$(".field");
                for (const field of fields) {
                    if (Number(field.dataset.row) === r && Number(field.dataset.col) === c) {
                        field.textContent = "O";
                        break;
                    }
                }

                highlightLastMove({ r, c });
                if (await isWinner()) {
                    return;
                }
                await evaluation();
            }
        }
    });

    let last = { row: undefined, col: undefined };

    board.addEventListener("mousemove", async (event) => {
        if (thinking) return;

        const target = event.target;
        if (target.classList.contains("field")) {
            const row = Number(target.dataset.row);
            const col = Number(target.dataset.col);
            if ((last.row === row && last.col === col) || BOARD[row][col] !== ".") {
                return;
            }
            last = { row, col };
            $("#hover").textContent = `(${last.row}, ${last.col})`;

            const result = window.evaluate(boardString({ r: row, c: col }));
            console.log("evaluation:", result);
            $("#evaluation").textContent = `evaluation: ${result.value}`;
        }
    });
}

window.onload = main;
