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
    }

    onMount(() => {
        reset();
    });

    const action = 1;

    action ? setInterval(frame, delay) : frame();
</script>

<svelte:window on:resize={reset} />

<footer>The aim of the game is to click on moving balls!</footer>

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

<span style="position: fixed; top: 0; right: 0">
    Field size: {wx}x{wy}
</span>

<div
    style:width="100%"
    style:height="60%"
    style:line-height="{size}px"
    style:outline="6px solid #ccc"
    style:border-radius="2px"
    bind:clientWidth={wx}
    bind:clientHeight={wy}
>
    {#key update}
        {#each balls as b}
            <span
                on:mousedown={() => clicked(b)}
                style:position="absolute"
                style:display="inline-block"
                style:user-select="none"
                style:font-size="{size}px"
                style:transform={`rotate(${b.angle}deg)`}
                style:left="{b.x}px"
                style:top="{b.y}px">{shapes[b.shape]}</span
            >
        {/each}
    {/key}
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
    <div style="margin-left: auto">
        <button on:click={reset}> Reset </button>
    </div>
</div>

<style>
    footer {
        font-size: 30px;
        padding-bottom: 1em;
    }
    .controls {
        display: flex;
        font-size: 20px;
        padding-bottom: 1em;
    }
    .controls span {
        vertical-align: top;
    }
    .scores {
        display: flex;
        font-size: 30px;
        padding-top: 1em;
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
