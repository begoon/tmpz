<script>
    import Char from "./Char.svelte";
    let w = 80;
    let h = 24;

    let vs = [];

    function generate() {
        const c = "1234567890";
        vs = new Array(h);
        for (let y = 0; y < h; y++) {
            const line = new Array(w);
            for (let x = 0; x < w; x++) {
                line[x] = c[(y + x) % c.length];
            }
            vs[y] = line;
        }
    }
    generate();

    function resize(vscreen, w, h) {
        if (!vscreen) return;
        generate();
        vw = parseFloat(getComputedStyle(vscreen).getPropertyValue("width"));
        vh = parseFloat(getComputedStyle(vscreen).getPropertyValue("height"));
        vh = window.innerHeight - 100;
        cw = vw / w;
        ch = vh / h;
    }

    let vscreen;
    let vw;
    let vh;
    let cw;
    let ch;
    $: {
        resize(vscreen, w, h);
        px = px;
        py = py;
        pc = pc;
    }

    let px = 0,
        py = 0,
        pc = "@";
</script>

<svelte:window on:resize={() => resize(vscreen, w, h)} />
<input type="range" bind:value={w} min="10" max="200" />
<input type="range" bind:value={h} min="10" max="100" />
<br />

<input type="number" bind:value={px} />
<input type="number" bind:value={py} />
<input type="text" bind:value={pc} />

{vs.length} x {vs[0].length} | {vw} x {vh} | {cw} x {ch}

<div style="background-color: cyan">
    <div style="--w: {w}; --h: {h}" bind:this={vscreen} class="vscreen">
        {#each vs as line, y}
            {#each line as c, x}
                {@const v = y == py && x == px ? pc : c}
                {@const color = y == py && x == px ? "red" : undefined}
                {@const background = y == py && x == px ? "yellow" : undefined}
                <Char w={cw} h={ch} c={v} {color} {background} />
            {/each}
        {/each}
    </div>
</div>

<style>
    div .vscreen {
        display: grid;
        grid-template-columns: repeat(var(--w), 1fr);
        grid-template-rows: repeat(var(--h), 1fr);
        border: 2px solid green;
        border-radius: 8px;
        height: 100%;
        width: 100%;
    }
    input[type="number"] {
        width: 3em;
    }
</style>
