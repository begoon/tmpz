<script lang="ts">
    import "animate.css";
    import "./app.css";
    import Counter from "./lib/Counter.svelte";
    import JSONer from "./lib/JSONer.svelte";

    // @ts-ignore
    const data = window.__DATA__;

    let ip = $state("?");

    async function getIP() {
        ip = "";
        ip = (await (await fetch("/endpoint/public-ip")).json()).ip;
    }

    const X = import.meta.env.VITE_X;
    console.log(X);

    let timeout = $state("4000ms");
    let message = $state("");

    let timer: number | null = null;
    let progress = $state(0);
</script>

<h1 class="text-5xl">[]root page[]</h1>
<Counter />
<JSONer value={data} />

<ul>
    <li><a class="underline" href="a/ABC">page a</a></li>
    <li><a class="underline" href="b/">page b</a></li>
</ul>

<button class="flex items-center justify-center p-4 bg-blue-300 border-2 border-blue-300 rounded-xl" onclick={getIP}>
    {#if ip}
        {ip}
    {:else}
        <div class="inline-block text-xs origin-center animate-spin">⏳</div>
    {/if}
</button>

<form class="mt-4" action="/report" method="post">
    <input type="text" name="message" class="w-full p-2 border-2 border-blue-300 rounded-xl" />
    <button class="flex items-center justify-center p-4 bg-blue-300 border-2 border-blue-300 rounded-xl">
        <div class="inline-block text-xs">report</div>
    </button>
</form>

<div class="flex">
    <input type="text" bind:value={timeout} class="w-[20em] p-2 border-2 border-blue-300 rounded-xl" />
    <button
        class="flex items-center justify-center p-2 bg-blue-300 border-2 border-blue-300 rounded-xl"
        onclick={() => {
            message = "...";
            let started = new Date().getTime();

            const elapsed = () => new Date().getTime() - started;

            timer = setInterval(() => {
                progress = elapsed() / 10;
                message = elapsed() + "ms";
            }, 10);
            fetch(`/paused/${timeout}`)
                .then((r) => r.text())
                .then((text) => {
                    timeout = elapsed() + "ms";
                    progress = 0;
                    message = text;
                    if (timer) {
                        clearInterval(timer);
                        timer = null;
                    }
                });
        }}
    >
        <div class="inline-block text-xs">invoke</div>
    </button>
    {#if message}
        <div class="p-2 bg-blue-300 border-2 border-blue-300 rounded-xl">{message}</div>
    {/if}
</div>
<div style="width: {progress}px" class="h-4 bg-slate-500 rounded-xl"></div>
