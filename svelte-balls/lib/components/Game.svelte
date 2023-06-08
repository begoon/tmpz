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
        for (const b of balls) {
            b.angle += 1;
            if (b.angle >= 360) b.angle = 0;
            b.x += b.dx * speed;
            if (b.x < 0 || b.x > wx - size) b.dx = -b.dx;
            b.y += b.dy * speed;
            if (b.y < 0 || b.y > wy - size) b.dy = -b.dy;
        }
        update += 1;
    };
    function clicked(b) {
        b.shape = (b.shape + 1) % shapes.length;
        b.scores += 1;
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
            {#each balls as b}
                <span
                    on:mousedown={() => clicked(b)}
                    on:touchstart={() => clicked(b)}
                    style:position="absolute"
                    style:display="inline-block"
                    style:user-select="none"
                    style:font-size="{size}px"
                    style:width="{size}px"
                    style:transform={`rotate(${b.angle}deg)`}
                    style:left="{b.x}px"
                    style:top="{b.y}px">{shapes[b.shape]}</span
                >
            {/each}
        {/key}
    </div>
    <div class="controls">
        <label>
            <span>
                Speed {speed}
            </span>
            <input type="range" bind:value={speed} min="1" max="9" />
        </label>

        <label style="margin-left: auto">
            <span>
                Ball size {size}
            </span>
            <input
                type="range"
                bind:value={size}
                min="10"
                max="200"
                on:change={reset}
            />
        </label>
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
        top: 0;
        right: 0;
        font-size: 16px;
        font-family: tahoma;
        padding: 2px;
        background: #eee;
        opacity: 0.7;
    }
    .controls {
        position: fixed;
        top: 0;
        left: 0;
        font-size: 20px;
        @media (max-width: 600px) {
            display: none;
        }
    }
    .controls span {
        vertical-align: top;
    }
    .scores {
        position: fixed;
        bottom: 0;
        left: 0;
        font-size: 30px;
        @media (max-width: 600px) {
            font-size: 20px;
        }
    }
    .reset {
        position: fixed;
        bottom: 0;
        right: 0;
        @media (max-width: 600px) {
            font-size: 20px;
        }
    }
    .title {
        position: fixed;
        bottom: 0;
        left: 50%;
        font-size: 30px;
        color: #fff;
        transform: translateX(-40%);
        @media (max-width: 600px) {
            display: none;
        }
    }
    button {
        font-size: 30px;
        grid-column: 1/2;
        margin-left: 30px;
        border: 2px solid #999;
        border-radius: 10px;
        border-style: outset;
        box-shadow: inset 0 0 10px #999;
        background: #eee;
    }
    input[type="range"] {
        appearance: none;
        width: 200px;
        height: 20px;
        background: #ddd;
        opacity: 0.7;
        border-radius: 10px;
    }
</style>
