<script>
    export let content;
</script>

<div class="board">
    {#each content as v}
        <div data-type={v} />
    {/each}
</div>

<style>
    .board {
        display: grid;
        height: 100%;
        border: 10px solid #aaa;
        grid-template-columns: repeat(var(--width), 1fr);
        grid-template-rows: repeat(var(--height), 1fr);
    }

    .board > * {
        display: inline-block;
        width: 100%;
        height: 100%;
        background-color: hsl(0, 0%, 90%);
    }

    .board > [data-type="player"] {
        background-color: green;
    }

    .board > [data-type="ball"] {
        background-color: black;
    }

    .board > [data-type="hunter"] {
        background-color: hsl(180, 50%, 50%);
    }

    .board > [data-type="border"] {
        background-color: hsl(50, 50%, 50%);
    }
</style>
