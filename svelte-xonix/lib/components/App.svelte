<script>
    import Board from "./Board.svelte";

    const BORDER_WIDTH = 2;
    const BORDER_HEIGHT = 2;

    const WIDTH = 64;
    const HEIGHT = 25;

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
        for (const ball of balls) {
            if (
                field.get(ball.x - 1, ball.y) == types.BORDER ||
                field.get(ball.x + 1, ball.y) == types.BORDER
            ) {
                ball.dx *= -1;
            }
            if (
                field.get(ball.x, ball.y - 1) == types.BORDER ||
                field.get(ball.x, ball.y + 1) == types.BORDER
            ) {
                ball.dy *= -1;
            }
            ball.x += ball.dx;
            ball.y += ball.dy;
        }
        updated = true;
    }

    const hunters = [{ x: WIDTH - 1, y: HEIGHT - 1, dx: -1, dy: -1 }];
    function move_hunters() {
        for (const v of hunters) {
            // ???
        }
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
