const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

const N = 15;

const BOARD = Array.from({ length: N }, () => Array.from({ length: N }, () => "."));

function boardString() {
    return BOARD.map((r) => r.join(""));
}

BOARD[7][7] = "X";
BOARD[7][8] = "O";

async function main() {
    const board = $("#board");

    let thinking = false;
    let lastMove = { r: -1, c: -1 };

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
        const data = JSON.stringify({ board: boardString() });
        const response = await (await fetch(`/end`, { method: "POST", body: data })).json();
        console.log("endgame data:", response);
        if (response.winner !== ".") {
            alert(`Game over! Winner: ${response.winner}`);
            return response.winner;
        }
        return undefined;
    }

    async function evaluation() {
        const data = JSON.stringify({ board: boardString() });
        const response = await (await fetch(`/eval`, { method: "POST", body: data })).json();
        console.log("evaluation:", response);
        $("#evaluation").textContent = `evaluation: ${response.value}`;
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
        if (thinking) return;

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

                const response = await (
                    await fetch(`/minimax`, {
                        method: "POST",
                        body: JSON.stringify({ depth: 3, board: boardString() }),
                    })
                ).json();

                updateThinking(false);

                console.log("minimax data:", response);
                const { r, c } = response.move;

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

            const data = JSON.stringify({ board: boardString(), move: { r: row, c: col } });

            const response = await (await fetch(`/eval`, { method: "POST", body: data })).json();
            console.log("evaluation:", response);
        }
    });
}

window.onload = main;
