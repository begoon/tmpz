<script>
    import Board from "./Board.svelte";

    const BORDER_WIDTH = 2;
    const BORDER_HEIGHT = 2;

    const WIDTH = 60;
    const HEIGHT = 30;

    const types = {
        PLAYER: "player",
        BALL: "ball",
        HUNTER: "hunter",
        BORDER: "border",
        FILLER: "filler",
    };

    class Field {
        constructor(width = WIDTH, height = HEIGHT) {
            this.width = width;
            this.height = height;
            this.field = [];
        }

        get(x, y) {
            return this.field[y * this.width + x];
        }

        set(x, y, value) {
            this.field[y * this.width + x] = value;
        }

        generate() {
            this.field = [...new Array(this.width * this.height)];
            for (let y = 0; y < HEIGHT; y++) {
                for (let x = 0; x < BORDER_WIDTH; x++) {
                    this.set(x, y, types.BORDER);
                    this.set(WIDTH - x - 1, y, types.BORDER);
                }
            }
            for (let x = 0; x < WIDTH; x++) {
                for (let y = 0; y < BORDER_HEIGHT; y++) {
                    this.set(x, y, types.BORDER);
                    this.set(x, HEIGHT - y - 1, types.BORDER);
                }
            }
        }
    }

    let player = {
        x: 0,
        y: 0,
    };

    let updated = false;

    function keydown(event) {
        const moves = {
            ArrowUp: { x: 0, y: -1 },
            ArrowDown: { x: 0, y: 1 },
            ArrowLeft: { x: -1, y: 0 },
            ArrowRight: { x: 1, y: 0 },
        };

        const { key } = event;
        const move = moves[key];
        if (!move) return;

        player.x += move.x;
        player.y += move.y;

        if (player.x < 0) player.x = 0;
        if (player.x >= WIDTH) player.x = WIDTH - 1;
        if (player.y < 0) player.y = 0;
        if (player.y >= HEIGHT) player.y = HEIGHT - 1;

        updated = true;
    }

    const R = () => Math.random();
    const IR = (max) => Math.floor(R());

    const balls = [];
    for (let i = 0; i < 5; i++) {
        balls.push({
            x: Math.ceil(R() * (WIDTH - BORDER_WIDTH * 2) + BORDER_WIDTH / 2),
            y: Math.ceil(
                R() * (HEIGHT - BORDER_HEIGHT * 2) + BORDER_HEIGHT / 2
            ),
            dx: R() < 0.5 ? -1 : 1,
            dy: R() < 0.5 ? -1 : 1,
        });
    }

    function move_balls() {
        for (const v of balls) {
            const n = { x: v.x + v.dx, y: v.y + v.dy };
            if (n.x < BORDER_WIDTH || n.x >= WIDTH - BORDER_WIDTH) v.dx *= -1;
            if (n.y < BORDER_HEIGHT || n.y >= HEIGHT - BORDER_HEIGHT)
                v.dy *= -1;
            v.x += v.dx;
            v.y += v.dy;
        }
        updated = true;
    }

    const hunters = [
        { x: WIDTH - 1, y: HEIGHT - 1, dx: 1, dy: 1 },
        { x: 0, y: HEIGHT - 1, dx: 1, dy: 1 },
    ];

    function move_hunters() {
        for (const v of hunters) {
            const n = { x: v.x + v.dx, y: v.y + v.dy };
            const ex = n.x < 0 || n.x >= WIDTH;
            const ey = n.y < 0 || n.y >= HEIGHT;
            if (ex) v.dx *= -1;
            if (ey) v.dy *= -1;
            if (!(ex || ey)) {
                const outside = field.get(n.x, n.y) != types.BORDER;
                const bx = v.x < BORDER_WIDTH || v.x >= WIDTH - BORDER_WIDTH;
                const by = v.y < BORDER_HEIGHT || v.y >= HEIGHT - BORDER_HEIGHT;
                if (outside) {
                    if (bx && by) {
                        R() < 0.5 ? (v.dx *= -1) : (v.dy *= -1);
                    } else {
                        if (bx) v.dx *= -1;
                        if (by) v.dy *= -1;
                    }
                }
            }
            v.x += v.dx;
            v.y += v.dy;
        }
        console.log(hunters[0]);
        updated = true;
    }

    const field = new Field();
    field.generate();

    let content = [];

    let last_balls_move = 0;

    requestAnimationFrame(function tick(time) {
        if (last_balls_move == 0) {
            last_balls_move = time;
        } else if (time - last_balls_move > 100) {
            last_balls_move = time;
            move_balls();
            move_hunters();
        }
        if (!updated) {
            requestAnimationFrame(tick);
            return;
        }
        const frame = new Field();
        frame.field = structuredClone(field.field);

        frame.set(player.x, player.y, types.PLAYER);
        for (const ball of balls) {
            frame.set(ball.x, ball.y, types.BALL);
        }
        for (const hunter of hunters) {
            frame.set(hunter.x, hunter.y, types.HUNTER);
        }
        content = frame.field;
        requestAnimationFrame(tick);
    });
</script>

<svelte:window on:keydown={keydown} />

<div class="screen">
    <div>Header</div>
    <Board --width={WIDTH} --heigth={HEIGHT} {content} />
    <div>
        {player.x}, {player.y}
    </div>
</div>

<style>
    .screen {
        height: 100vh;
        width: 100%;
        border: 8px solid #eee;
        display: flex;
        flex-direction: column;
    }
    :global(*) {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
</style>
