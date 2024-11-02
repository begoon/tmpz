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
    console.log(import.meta);
    console.log("aaa");
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
