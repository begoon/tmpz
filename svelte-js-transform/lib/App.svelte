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
    <div class="inner">
        <div style="height: 100%; border: 1px solid brown">
            <input
                type="range"
                bind:value={angleY}
                min="0"
                max="180"
                step="1"
                orient="vertical"
            />
        </div>
        <div
            class="scene"
            on:pointerdown={down}
            on:pointerup={up}
            on:pointermove={move}
        >
            <div class="text" style="--angleX: {angleX}; --angleY: {angleY}">
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
    </div>
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
        height: 100vh;
        border: 1px solid red;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        user-select: none;
    }
    div.inner {
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    div.scene {
        perspective: 1000px;
        width: 100%;
        height: 100%;
        border: 1px solid green;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    div.text {
        transform: rotateX(calc(var(--angleY) * 1deg))
            rotateY(calc(var(--angleX) * 1deg));
        max-width: 90vw;
        width: 100%;
        height: 100%;
        border: 1px solid blue;
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
