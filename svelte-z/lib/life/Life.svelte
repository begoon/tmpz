<script>
    import { onDestroy } from "svelte";

    let last_time = window.performance.now();
    let frame;

    let field = [];

    (function update() {
        frame = requestAnimationFrame(update);

        const time = window.performance.now();
        const elapsed = time - last_time;

        if (elapsed < 1000) return;
        last_time = time;

        field = field.map((row, i) =>
            row.map((cell, j) => {
                const neighbors = [
                    field[i - 1]?.[j - 1],
                    field[i - 1]?.[j],
                    field[i - 1]?.[j + 1],
                    field[i][j - 1],
                    field[i][j + 1],
                    field[i + 1]?.[j - 1],
                    field[i + 1]?.[j],
                    field[i + 1]?.[j + 1],
                ].filter(Boolean).length;
                return neighbors === 3 || (cell && neighbors === 2);
            })
        );
    })();

    onDestroy(() => {
        cancelAnimationFrame(frame);
    });

    function randomize() {
        field = Array.from({ length: 150 }, () =>
            Array.from({ length: 150 }, () => Math.random() < 0.3)
        );
    }

    randomize();
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div class="grid h-screen place-items-center" on:click={randomize}>
    <table>
        {#each field as row, i}
            <tr>
                {#each row as cell, j}
                    <td
                        class="p-0 m-0 w-[4px] h-[4px]"
                        style="background: {cell ? 'green' : 'white'}"
                    />
                {/each}
            </tr>
        {/each}
    </table>
</div>
