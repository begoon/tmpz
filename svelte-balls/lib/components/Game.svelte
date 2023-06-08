<script>
    import { onMount } from "svelte";

    let shapes = ["🎾", "🏐", "⚽️", "🏀"];

    const delay = 10;
    let speed = 3;

    let wx = 0;
    let wy = 0;
    let size = 150;

    let balls = [];
    let update = 0;

    const frame = () => {
        for (const ball of balls) {
            ball.angle += 1;
            if (ball.angle >= 360) ball.angle = 0;
            ball.x += ball.dx * speed;
            if (ball.x < 0 || ball.x > wx - size) ball.dx = -ball.dx;
            ball.y += ball.dy * speed;
            if (ball.y < 0 || ball.y > wy - size) ball.dy = -ball.dy;
        }
        update += 1;
    };
    function clicked(ball) {
        ball.shape = (ball.shape + 1) % shapes.length;
        ball.scores += 1;
        update += 1;
    }
    const r = () => Math.random();
    function reset() {
        balls = [];
        const n = 2 + Math.ceil(r() * 2);
        for (let i = 0; i < n; ++i) {
            const ball = {
                x: r() * (wx - size),
                y: r() * (wy - size),
                dx: r() < 0.5 ? 1 : -1,
                dy: r() < 0.5 ? 1 : -1,
                shape: Math.floor(r() * shapes.length),
                scores: 0,
                angle: 0,
            };
            balls.push(ball);
        }
        height = window.innerHeight;
    }

    onMount(() => {
        reset();
    });

    const action = 1;

    action ? setInterval(frame, delay) : frame();

    $: height = window.innerHeight;
</script>

<svelte:window on:resize={reset} />

<span class="dimentions">
    {wx}x{wy}
</span>

<div style:height="{height}px">
    <div
        style:width="100%"
        style:height="calc(100% - 60px)"
        style:top="30px"
        style:bottom="30px"
        style:line-height="{size}px"
        style:text-align="center"
        style:border-radius="2px"
        style:overflow="clip"
        bind:clientWidth={wx}
        bind:clientHeight={wy}
    >
        {#key update}
            {#each balls as ball}
                <span
                    on:mousedown={() => clicked(ball)}
                    on:touchstart={() => clicked(ball)}
                    style:position="absolute"
                    style:display="inline-block"
                    style:user-select="none"
                    style:font-size="{size}px"
                    style:width="{size}px"
                    style:transform={`rotate(${ball.angle}deg)`}
                    style:left="{ball.x}px"
                    style:top="{ball.y}px">{shapes[ball.shape]}</span
                >
            {/each}
        {/key}
    </div>
    <div class="controls">
        <b>
            Speed {speed}
        </b>
        <input type="range" bind:value={speed} min="1" max="9" />
        <b>
            Ball size {size}
        </b>
        <input
            type="range"
            bind:value={size}
            min="10"
            max="200"
            on:change={reset}
        />
    </div>
    <div class="scores">
        <div>
            Scores:
            {#key update}
                {#each balls as b}
                    <span>
                        {shapes[b.shape]}
                        {b.scores}
                    </span>
                {/each}
            {/key}
        </div>
    </div>
    <div class="title">Click on the balls to change their shape</div>
    <button on:click={reset} class="reset">Reset</button>
</div>

<style>
    .dimentions {
        position: fixed;
        bottom: 0;
        right: 0;
        font-size: 16px;
        font-family: tahoma;
        padding: 2px;
        background: #eee;
        opacity: 0.7;
        @media (max-width: 600px) {
            font-size: 20px;
            transform: translateX(-50%);
            left: 50%;
            text-align: center;
            width: 100%;
        }
    }
    .controls {
        position: fixed;
        bottom: 0;
        left: 0;
        font-size: 24px;
        font-weight: 200;
        text-transform: lowercase;
        @media (max-width: 600px) {
            display: none;
        }
    }
    .controls b {
        vertical-align: top;
    }
    .scores {
        position: fixed;
        top: 0;
        left: 0;
        font-size: 30px;
        @media (max-width: 600px) {
            font-size: 20px;
        }
    }
    .reset {
        position: fixed;
        top: 0;
        right: 0;
        font-size: 25px;
        @media (max-width: 600px) {
            font-size: 20px;
        }
    }
    .title {
        position: fixed;
        top: 0;
        left: 50%;
        font-size: 30px;
        color: #fff;
        transform: translateX(-40%);
        @media (max-width: 600px) {
            display: none;
        }
    }
    button {
        border: 1px solid #999;
        border-radius: 6px;
        box-shadow: inset 0 0 10px #999;
    }
    input[type="range"] {
        appearance: none;
        width: 200px;
        height: 20px;
        opacity: 0.6;
        border-radius: 6px;
    }
</style>
