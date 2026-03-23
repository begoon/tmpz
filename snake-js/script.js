const CELL = 16;
const TICK = 110;

const COLOR = {
    border: "#3d3d5c",
    field: "#1a1a2e",
    grid: "rgba(255,255,255,0.03)",
    snake: "#00ff88",
    head: "#00cc6a",
    rabbit: "#ff4757",
    text: "#ffffff",
    overlay: "rgba(0,0,0,0.7)",
};

let canvas, ctx;
let cols, rows;
let snake, dir, nextDir;
let rabbit;
let dead, score, growth;
let lastTick;
let gpRestartWas = false;

function init() {
    canvas = document.getElementById("game");
    ctx = canvas.getContext("2d");
    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("keydown", onKey);
    window.addEventListener("gamepadconnected", (e) => console.log("gamepad connected:", e.gamepad.id));
    requestAnimationFrame(loop);
}

function resize() {
    cols = Math.floor(window.innerWidth / CELL);
    rows = Math.floor(window.innerHeight / CELL);
    canvas.width = cols * CELL;
    canvas.height = rows * CELL;
    start();
}

function start() {
    const cx = Math.floor(cols / 2);
    const cy = Math.floor(rows / 2);
    snake = [];
    for (let i = 0; i < 5; i++) snake.push({ x: cx - i, y: cy });
    dir = { x: 1, y: 0 };
    nextDir = { x: 1, y: 0 };
    growth = 0;
    dead = false;
    score = 0;
    lastTick = performance.now();
    placeRabbit();
}

function placeRabbit() {
    const taken = new Set(snake.map((s) => s.x + "," + s.y));
    const free = [];
    for (let x = 1; x < cols - 1; x++)
        for (let y = 1; y < rows - 1; y++) if (!taken.has(x + "," + y)) free.push({ x, y });
    if (!free.length) return;
    rabbit = free[Math.floor(Math.random() * free.length)];
}

function onKey(e) {
    if (dead) {
        if (e.code === "Space" || e.code === "Enter") start();
        return;
    }
    switch (e.code) {
        case "ArrowUp":
        case "KeyW":
            if (!dir.y) nextDir = { x: 0, y: -1 };
            break;
        case "ArrowDown":
        case "KeyS":
            if (!dir.y) nextDir = { x: 0, y: 1 };
            break;
        case "ArrowLeft":
        case "KeyA":
            if (!dir.x) nextDir = { x: -1, y: 0 };
            break;
        case "ArrowRight":
        case "KeyD":
            if (!dir.x) nextDir = { x: 1, y: 0 };
            break;
    }
    e.preventDefault();
}

function pollGamepad() {
    const pads = navigator.getGamepads();
    if (!pads) return;
    for (const gp of pads) {
        if (!gp) continue;

        if (!dead) {
            // D-pad
            if (gp.buttons[12]?.pressed && !dir.y) nextDir = { x: 0, y: -1 };
            if (gp.buttons[13]?.pressed && !dir.y) nextDir = { x: 0, y: 1 };
            if (gp.buttons[14]?.pressed && !dir.x) nextDir = { x: -1, y: 0 };
            if (gp.buttons[15]?.pressed && !dir.x) nextDir = { x: 1, y: 0 };

            // Left stick
            const lx = gp.axes[0];
            const ly = gp.axes[1];
            const dz = 0.5;
            if (Math.abs(lx) > Math.abs(ly)) {
                if (lx < -dz && !dir.x) nextDir = { x: -1, y: 0 };
                if (lx > dz && !dir.x) nextDir = { x: 1, y: 0 };
            } else {
                if (ly < -dz && !dir.y) nextDir = { x: 0, y: -1 };
                if (ly > dz && !dir.y) nextDir = { x: 0, y: 1 };
            }
        }

        // A button restart (edge-triggered)
        const aPressed = gp.buttons[0]?.pressed;
        if (dead && aPressed && !gpRestartWas) start();
        gpRestartWas = aPressed;
    }
}

function update(now) {
    if (dead) return;
    if (now - lastTick < TICK) return;
    lastTick += TICK;

    dir = { ...nextDir };
    const h = { x: snake[0].x + dir.x, y: snake[0].y + dir.y };

    // Border collision
    if (h.x <= 0 || h.x >= cols - 1 || h.y <= 0 || h.y >= rows - 1) {
        dead = true;
        return;
    }

    // Self collision
    for (const s of snake)
        if (s.x === h.x && s.y === h.y) {
            dead = true;
            return;
        }

    snake.unshift(h);

    if (rabbit && h.x === rabbit.x && h.y === rabbit.y) {
        growth += 3;
        score++;
        placeRabbit();
    }

    if (growth > 0) growth--;
    else snake.pop();
}

function draw() {
    // Field
    ctx.fillStyle = COLOR.field;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid lines
    ctx.strokeStyle = COLOR.grid;
    ctx.lineWidth = 1;
    for (let x = 1; x < cols; x++) {
        ctx.beginPath();
        ctx.moveTo(x * CELL + 0.5, CELL);
        ctx.lineTo(x * CELL + 0.5, (rows - 1) * CELL);
        ctx.stroke();
    }
    for (let y = 1; y < rows; y++) {
        ctx.beginPath();
        ctx.moveTo(CELL, y * CELL + 0.5);
        ctx.lineTo((cols - 1) * CELL, y * CELL + 0.5);
        ctx.stroke();
    }

    // Border
    ctx.fillStyle = COLOR.border;
    for (let x = 0; x < cols; x++) {
        ctx.fillRect(x * CELL, 0, CELL, CELL);
        ctx.fillRect(x * CELL, (rows - 1) * CELL, CELL, CELL);
    }
    for (let y = 1; y < rows - 1; y++) {
        ctx.fillRect(0, y * CELL, CELL, CELL);
        ctx.fillRect((cols - 1) * CELL, y * CELL, CELL, CELL);
    }

    // Rabbit
    if (rabbit) {
        ctx.fillStyle = COLOR.rabbit;
        ctx.beginPath();
        const rx = rabbit.x * CELL + CELL / 2;
        const ry = rabbit.y * CELL + CELL / 2;
        ctx.arc(rx, ry, CELL / 2 - 2, 0, Math.PI * 2);
        ctx.fill();
    }

    // Snake
    for (let i = snake.length - 1; i >= 0; i--) {
        ctx.fillStyle = i === 0 ? COLOR.head : COLOR.snake;
        ctx.fillRect(snake[i].x * CELL + 1, snake[i].y * CELL + 1, CELL - 2, CELL - 2);
    }

    // Score
    ctx.fillStyle = COLOR.text;
    ctx.font = "bold 14px monospace";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText("Score: " + score, CELL + 6, CELL + 4);

    // Game over overlay
    if (dead) {
        ctx.fillStyle = COLOR.overlay;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const mx = canvas.width / 2;
        const my = canvas.height / 2;

        ctx.fillStyle = COLOR.rabbit;
        ctx.font = "bold 36px monospace";
        ctx.fillText("GAME OVER", mx, my - 30);

        ctx.fillStyle = COLOR.text;
        ctx.font = "20px monospace";
        ctx.fillText("Score: " + score, mx, my + 10);

        ctx.font = "14px monospace";
        ctx.fillStyle = "rgba(255,255,255,0.6)";
        ctx.fillText("SPACE / Enter / \uD83C\uDFAE A  to restart", mx, my + 45);
    }
}

function loop(now) {
    pollGamepad();
    update(now);
    draw();
    requestAnimationFrame(loop);
}

window.addEventListener("load", init);
