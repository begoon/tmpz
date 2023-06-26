<script>
    let angleX = 0;
    let angleY = 0;

    let tracking = false;
    let lastX = 0;
    let lastY = 0;

    function down(e) {
        tracking = true;
        lastX = e.clientX;
        lastY = e.clientY;
    }
    function up() {
        tracking = false;
    }
    function move(event) {
        if (!tracking) return;
        const deltaX = lastX - event.clientX;
        lastX = event.clientX;
        angleX -= deltaX;

        const deltaY = lastY - event.clientY;
        lastY = event.clientY;
        angleY += deltaY;
    }
</script>

<div class="main">
    <input
        type="range"
        bind:value={angleY}
        min="0"
        max="180"
        step="1"
        orient="vertical"
    />
    <div
        class="scene"
        on:pointerdown={down}
        on:pointerup={up}
        on:pointermove={move}
    >
        <div class="rotor" style="--angleX: {angleX}; --angleY: {angleY}">
            <svg
                viewBox="0 0 58 10"
                width="100%"
                height="100%"
                style="font-size: 10px;"
            >
                <text y="8">Alexander</text>
            </svg>
        </div>
    </div>
    <div />
    <input type="range" bind:value={angleX} min="0" max="180" step="1" />
</div>

<svelte:window />

<style>
    :global(*) {
        font-family: Orbitron, sans-serif;
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        overflow: hidden;
    }
    div.main {
        height: 100dvh;
        border: 0px solid red;
        display: grid;
        grid-template-columns: auto 1fr;
        grid-template-rows: 1fr auto;
        user-select: none;
    }
    div.scene {
        perspective: 1000px;
        border: 0px solid green;
        display: flex;
        padding: 1em;
    }
    div.rotor {
        transform: rotateX(calc(var(--angleY) * 1deg))
            rotateY(calc(var(--angleX) * 1deg));
        width: 100%;
        border: 1px solid hsl(0, 0%, 0%, 0.5);
        border-radius: 0.5em;
    }
    svg {
        border: 0px solid yellow;
    }
    input[type="range"] {
        width: 100%;
    }
    input[type="range"][orient="vertical"] {
        writing-mode: bt-lr; /* IE */
        -webkit-appearance: slider-vertical; /* Chromium */
        width: 1.2em;
        height: 100%;
    }
</style>
